# Copyright (c) 2015-2016 Codethink Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy.orm import aliased
from wsme.exc import ClientSideError

from storyboard._i18n import _
from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import boards
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import users as users_api
from storyboard.db import models


def _worklist_get(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.Worklist).filter_by(id=id)
    return query.first()


def get(worklist_id):
    return _worklist_get(worklist_id)


def _build_worklist_query(title=None, creator_id=None, project_id=None,
                          archived=False, user_id=None, session=None,
                          current_user=None, hide_lanes=True, item_type=None,
                          story_id=None, task_id=None, subscriber_id=None):
    query = api_base.model_query(models.Worklist, session=session).distinct()

    query = api_base.apply_query_filters(query=query,
                                         model=models.Worklist,
                                         title=title,
                                         creator_id=creator_id,
                                         project_id=project_id)

    query = api_base.filter_private_worklists(query, current_user)

    # Filter by lists that a given user has permissions to use
    if user_id:
        worklist_permissions = aliased(models.worklist_permissions)
        permissions = aliased(models.Permission)
        user_permissions = aliased(models.user_permissions)
        users = aliased(models.User)
        query = query.join(
            (worklist_permissions,
             models.Worklist.id == worklist_permissions.c.worklist_id)
        )
        query = query.join(
            (permissions,
             worklist_permissions.c.permission_id == permissions.id)
        )
        query = query.join(
            (user_permissions,
             permissions.id == user_permissions.c.permission_id)
        )
        query = query.join((users, user_permissions.c.user_id == users.id))
        query = query.filter(users.id == user_id)

    # Filter by whether or not we want archived lists
    query = query.filter(models.Worklist.archived == archived)

    # Filter by story id
    if story_id:
        query = query.join(models.WorklistItem)
        stories = query.filter(models.WorklistItem.item_type == 'story')
        tasks = query.filter(models.WorklistItem.item_type == 'task')
        if item_type == 'story':
            query = stories.filter(models.WorklistItem.item_id == story_id)
        elif item_type == 'task':
            tasks = tasks.join(
                (models.Task, models.WorklistItem.item_id == models.Task.id))
            query = tasks.filter(models.Task.story_id == story_id)
        else:
            stories = stories.filter(models.WorklistItem.item_id == story_id)
            tasks = tasks.join(
                (models.Task, models.WorklistItem.item_id == models.Task.id))
            tasks = tasks.filter(models.Task.story_id == story_id)
            query = stories.union(tasks)

    # Filter by task id
    if task_id:
        items = aliased(models.WorklistItem)
        query = query.join((items, models.Worklist.id == items.list_id))
        query = query.filter(items.item_type == 'task')
        query = query.filter(items.item_id == task_id)

    # Filter by subscriber id
    if subscriber_id is not None:
        subs = api_base.model_query(models.Subscription)
        subs = api_base.apply_query_filters(query=subs,
                                            model=models.Subscription,
                                            target_type='worklist',
                                            user_id=subscriber_id)
        subs = subs.subquery()
        query = query.join(subs, subs.c.target_id == models.Worklist.id)

    return query


def get_all(title=None, creator_id=None, project_id=None, board_id=None,
            user_id=None, story_id=None, task_id=None, subscriber_id=None,
            sort_field=None, sort_dir=None, session=None, offset=None,
            limit=None, archived=False, current_user=None, hide_lanes=True,
            item_type=None, **kwargs):
    if sort_field is None:
        sort_field = 'id'
    if sort_dir is None:
        sort_dir = 'asc'

    if board_id is not None:
        board = boards.get(board_id)
        if board is None:
            return []
        return [lane.worklist for lane in board.lanes
                if visible(lane.worklist, current_user)]

    query = _build_worklist_query(title=title,
                                  creator_id=creator_id,
                                  project_id=project_id,
                                  user_id=user_id,
                                  subscriber_id=subscriber_id,
                                  archived=archived,
                                  session=session,
                                  current_user=current_user,
                                  hide_lanes=hide_lanes,
                                  item_type=item_type,
                                  story_id=story_id,
                                  task_id=task_id)

    query = api_base.paginate_query(query=query,
                                    model=models.Worklist,
                                    limit=limit,
                                    offset=offset,
                                    sort_key=sort_field,
                                    sort_dir=sort_dir)
    return query.all()


def get_count(title=None, creator_id=None, project_id=None, board_id=None,
              user_id=None, story_id=None, task_id=None, subscriber_id=None,
              session=None, archived=False, current_user=None,
              hide_lanes=True, item_type=None, **kwargs):
    if board_id is not None:
        board = boards.get(board_id)
        if board is None:
            return 0
        lists = [lane.worklist for lane in board.lanes
                 if visible(lane.worklist, current_user)]
        return len(lists)

    query = _build_worklist_query(title=title,
                                  creator_id=creator_id,
                                  project_id=project_id,
                                  user_id=user_id,
                                  subscriber_id=subscriber_id,
                                  archived=archived,
                                  session=session,
                                  current_user=current_user,
                                  hide_lanes=hide_lanes,
                                  story_id=story_id,
                                  task_id=task_id,
                                  item_type=item_type)
    return query.count()


def get_visible_items(worklist, current_user=None):
    stories = worklist.items.filter(models.WorklistItem.item_type == 'story')
    stories = stories.join(
        (models.Story, models.Story.id == models.WorklistItem.item_id))
    stories = api_base.filter_private_stories(stories, current_user)

    tasks = worklist.items.filter(models.WorklistItem.item_type == 'task')
    tasks = tasks.join(
        (models.Task, models.Task.id == models.WorklistItem.item_id))
    tasks = tasks.outerjoin(models.Story)
    tasks = api_base.filter_private_stories(tasks, current_user)

    return stories.union(tasks)


def create(values):
    return api_base.entity_create(models.Worklist, values)


def update(worklist_id, values):
    return api_base.entity_update(models.Worklist, worklist_id, values)


def has_item(worklist, item_type, item_id):
    for item in worklist.items:
        if item.item_type == item_type and item.item_id == item_id:
            return True
    return False


def add_item(worklist_id, item_id, item_type, list_position,
             current_user=None):
    worklist = _worklist_get(worklist_id)
    if worklist is None:
        raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    # Check if this item has an archived card in this worklist to restore
    archived = get_item_by_item_id(
        worklist, item_type, item_id, archived=True)
    if archived:
        update = {
            'archived': False,
            'list_position': list_position
        }
        api_base.entity_update(models.WorklistItem, archived.id, update)
        return worklist

    # If this worklist is a lane, check if the item has an archived card
    # somewhere in the board to restore
    if is_lane(worklist):
        board = boards.get_from_lane(worklist)
        archived = boards.get_card(board, item_type, item_id, archived=True)
        if archived:
            update = {
                'archived': False,
                'list_id': worklist_id,
                'list_position': list_position
            }
            api_base.entity_update(models.WorklistItem, archived.id, update)
            return worklist

    # Create a new card
    if item_type == 'story':
        item = stories_api.story_get(item_id, current_user=current_user)
    elif item_type == 'task':
        item = tasks_api.task_get(item_id, current_user=current_user)
    else:
        raise ClientSideError(_("An item in a worklist must be either a "
                                "story or a task"))

    if item is None:
        raise exc.NotFound(_("%(type)s %(id)s not found") %
                           {'type': item_type, 'id': item_id})

    item_dict = {
        'list_id': worklist_id,
        'item_id': item_id,
        'item_type': item_type,
        'list_position': list_position
    }
    worklist_item = api_base.entity_create(models.WorklistItem, item_dict)

    if worklist.items is None:
        worklist.items = [worklist_item]
    else:
        worklist.items.append(worklist_item)

    return worklist


def get_item_by_id(item_id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.WorklistItem).filter_by(id=str(item_id))

    return query.first()


def get_item_at_position(worklist_id, list_position):
    session = api_base.get_session()
    query = session.query(models.WorklistItem).filter_by(
        list_id=worklist_id, list_position=list_position)

    return query.first()


def get_item_by_item_id(worklist, item_type, item_id, archived):
    session = api_base.get_session()
    query = session.query(models.WorklistItem).filter_by(
        list_id=worklist.id, item_type=item_type,
        item_id=item_id, archived=archived)

    return query.first()


def normalize_positions(worklist):
    for item in worklist.items:
        if item.archived:
            item.list_position = 99999
    items = worklist.items.order_by(
        models.WorklistItem.list_position)
    for position, item in enumerate(items):
        if not item.archived:
            item.list_position = position


def move_item(worklist_id, item_id, list_position, list_id=None):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        item = get_item_by_id(item_id, session)
        old_pos = item.list_position
        item.list_position = list_position

        if old_pos == list_position and list_id == item.list_id:
            return

        old_list = _worklist_get(item.list_id)

        if list_id is not None and list_id != item.list_id:
            # Item has moved from one list into a different one.
            # Move the item and clean up the positions.
            new_list = _worklist_get(list_id)
            old_list.items.remove(item)
            old_list.items = old_list.items.order_by(
                models.WorklistItem.list_position)
            for list_item in old_list.items[old_pos:]:
                list_item.list_position -= 1
            normalize_positions(old_list)

            new_list.items = new_list.items.order_by(
                models.WorklistItem.list_position)
            for list_item in new_list.items[list_position:]:
                list_item.list_position += 1
            new_list.items.append(item)
            normalize_positions(new_list)
        else:
            # Item has changed position in the list.
            # Update the position of every item between the original
            # position and the final position.
            old_list.items = old_list.items.order_by(
                models.WorklistItem.list_position)
            if old_pos > list_position:
                direction = 'down'
                modified = old_list.items[list_position:old_pos + 1]
            else:
                direction = 'up'
                modified = old_list.items[old_pos:list_position + 1]

            for list_item in modified:
                if direction == 'up' and list_item != item:
                    list_item.list_position -= 1
                elif direction == 'down' and list_item != item:
                    list_item.list_position += 1

            normalize_positions(old_list)


def update_item(item_id, updated):
    return api_base.entity_update(models.WorklistItem, item_id, updated)


def is_lane(worklist):
    lanes = api_base.entity_get_all(models.BoardWorklist,
                                    list_id=worklist.id)
    if lanes:
        return True
    return False


def get_owners(worklist):
    for permission in worklist.permissions:
        if permission.codename == 'edit_worklist':
            return [user.id for user in permission.users]


def get_users(worklist):
    for permission in worklist.permissions:
        if permission.codename == 'move_items':
            return [user.id for user in permission.users]


def get_permissions(worklist, user_id):
    user = users_api.user_get(user_id)
    if user is not None:
        return [permission.codename for permission in worklist.permissions
                if permission in user.permissions]
    return []


def create_permission(worklist_id, permission_dict, session=None):
    worklist = _worklist_get(worklist_id, session=session)
    users = permission_dict.pop('users')
    permission = api_base.entity_create(
        models.Permission, permission_dict, session=session)
    worklist.permissions.append(permission)
    for user_id in users:
        user = users_api.user_get(user_id, session=session)
        user.permissions.append(permission)
    return permission


def update_permission(worklist_id, permission_dict):
    worklist = _worklist_get(worklist_id)
    id = None
    for permission in worklist.permissions:
        if permission.codename == permission_dict['codename']:
            id = permission.id
    users = permission_dict.pop('users')
    permission_dict['users'] = []
    for user_id in users:
        user = users_api.user_get(user_id)
        permission_dict['users'].append(user)

    if id is None:
        raise ClientSideError(_("Permission %s does not exist")
                              % permission_dict['codename'])
    return api_base.entity_update(models.Permission, id, permission_dict)


def visible(worklist, user=None, hide_lanes=False):
    if hide_lanes:
        if is_lane(worklist):
            return False
    if not worklist:
        return False
    if is_lane(worklist):
        board = boards.get_from_lane(worklist)
        permissions = boards.get_permissions(board, user)
        if board.private:
            return any(name in permissions
                       for name in ['edit_board', 'move_cards'])
        return not board.private
    if user and worklist.private:
        permissions = get_permissions(worklist, user)
        return any(name in permissions
                   for name in ['edit_worklist', 'move_items'])
    return not worklist.private


def editable(worklist, user=None):
    if not worklist:
        return False
    if not user:
        return False
    if is_lane(worklist):
        board = boards.get_from_lane(worklist)
        permissions = boards.get_permissions(board, user)
        return any(name in permissions
                   for name in ['edit_board', 'move_cards'])
    return 'edit_worklist' in get_permissions(worklist, user)


def editable_contents(worklist, user=None):
    if not worklist:
        return False
    if not user:
        return False
    if is_lane(worklist):
        board = boards.get_from_lane(worklist)
        permissions = boards.get_permissions(board, user)
        return any(name in permissions
                   for name in ['edit_board', 'move_cards'])
    permissions = get_permissions(worklist, user)
    return any(name in permissions
               for name in ['edit_worklist', 'move_items'])


def get_filter(filter_id):
    return api_base.entity_get(models.WorklistFilter, filter_id)


def create_filter(worklist_id, filter_dict):
    criteria = filter_dict.pop('filter_criteria')
    filter_dict['list_id'] = worklist_id
    filter = api_base.entity_create(models.WorklistFilter, filter_dict)

    # Create criteria for the filter
    filter = api_base.entity_get(models.WorklistFilter, filter.id)
    filter.criteria = []
    for criterion in criteria:
        criterion_dict = criterion.as_dict()
        criterion_dict['filter_id'] = filter.id
        filter.criteria.append(
            api_base.entity_create(models.FilterCriterion, criterion_dict))

    return filter


def update_filter(filter_id, update):
    old_filter = api_base.entity_get(models.WorklistFilter, filter_id)
    if 'filter_criteria' in update:
        # Change the criteria for this filter. If an ID is provided, change
        # the criterion to match the provided criterion. If no ID is provided,
        # create a new criterion and add it to the filter.
        for criterion in update['filter_criteria']:
            criterion_dict = criterion.as_dict(omit_unset=True)
            if 'id' in criterion_dict:
                id = criterion_dict.pop('id')
                api_base.entity_update(models.FilterCriterion,
                                       id, criterion_dict)
            else:
                created = api_base.entity_create(models.FilterCriterion,
                                                 criterion_dict)
                criterion.id = created
                old_filter.criteria.append(created)

        # Remove criteria which aren't in the provided set
        new_ids = [criterion.id for criterion in update['filter_criteria']]
        for criterion in old_filter.criteria:
            if criterion.id not in new_ids:
                old_filter.criteria.remove(criterion)
        del update['filter_criteria']

    return api_base.entity_update(models.WorklistFilter, filter_id, update)


def delete_filter(filter_id):
    filter = api_base.entity_get(models.WorklistFilter, filter_id)
    for criterion in filter.criteria:
        api_base.entity_hard_delete(models.FilterCriterion, criterion.id)
    api_base.entity_hard_delete(models.WorklistFilter, filter_id)


def translate_criterion_to_field(criterion):
    criterion_fields = {
        'Project': 'project_id',
        'ProjectGroup': 'project_group_id',
        'Story': 'story_id',
        'User': 'assignee_id',
        'StoryStatus': 'status',
        'Tags': 'tags',
        'TaskStatus': 'status',
        'Text': 'title'
    }

    if criterion.field not in criterion_fields:
        return None
    return criterion_fields[criterion.field]


def filter_stories(worklist, filters):
    filter_queries = []
    for filter in filters:
        subquery = api_base.model_query(models.Story.id).distinct().subquery()
        query = api_base.model_query(models.StorySummary)
        query = query.join(subquery, models.StorySummary.id == subquery.c.id)
        query = query.outerjoin(models.Task,
                                models.Project,
                                models.project_group_mapping,
                                models.ProjectGroup)
        for criterion in filter.criteria:
            attr = translate_criterion_to_field(criterion)
            if hasattr(models.StorySummary, attr):
                model = models.StorySummary
            else:
                if attr in ('assignee_id', 'project_id'):
                    model = models.Task
                elif attr == 'project_group_id':
                    model = models.ProjectGroup
                    attr = 'id'
                else:
                    continue

            if attr == 'tags':
                if criterion.negative:
                    query = query.filter(
                        ~models.StorySummary.tags.any(
                            models.StoryTag.name.in_([criterion.value])))
                else:
                    query = query.filter(
                        models.StorySummary.tags.any(
                            models.StoryTag.name.in_([criterion.value])))
                continue

            if criterion.negative:
                query = query.filter(
                    getattr(model, attr) != criterion.value)
            else:
                query = query.filter(
                    getattr(model, attr) == criterion.value)
        filter_queries.append(query)

    if len(filter_queries) > 1:
        query = filter_queries[0]
        query = query.union(*filter_queries[1:])
        return query.all()
    elif len(filter_queries) == 1:
        return filter_queries[0].all()
    else:
        return []


def filter_tasks(worklist, filters):
    filter_queries = []
    for filter in filters:
        query = api_base.model_query(models.Task)
        query = query.outerjoin(models.Project,
                                models.project_group_mapping,
                                models.ProjectGroup)
        for criterion in filter.criteria:
            attr = translate_criterion_to_field(criterion)
            if hasattr(models.Task, attr):
                model = models.Task
            elif attr == 'project_group_id':
                model = models.ProjectGroup
                attr = 'id'
            else:
                continue
            if criterion.negative:
                query = query.filter(getattr(model, attr) != criterion.value)
            else:
                query = query.filter(getattr(model, attr) == criterion.value)
        filter_queries.append(query)

    if len(filter_queries) > 1:
        query = filter_queries[0]
        query = query.union(*filter_queries[1:])
        return query.all()
    elif len(filter_queries) == 1:
        return filter_queries[0].all()
    else:
        return []


def filter_items(worklist):
    story_filters = [f for f in worklist.filters if f.type == 'Story']
    task_filters = [f for f in worklist.filters if f.type == 'Task']

    filtered_stories = []
    filtered_tasks = []
    if story_filters:
        filtered_stories = filter_stories(worklist, story_filters)
    if task_filters:
        filtered_tasks = filter_tasks(worklist, task_filters)

    items = []
    for story in filtered_stories:
        items.append({
            'list_id': worklist.id,
            'item_id': story.id,
            'item_type': 'story',
            'list_position': 0,
            'display_due_date': None
        })
    for task in filtered_tasks:
        items.append({
            'list_id': worklist.id,
            'item_id': task.id,
            'item_type': 'task',
            'list_position': 0,
            'display_due_date': None
        })

    return items
