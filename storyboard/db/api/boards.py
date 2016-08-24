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

from sqlalchemy.orm import aliased, subqueryload
from wsme.exc import ClientSideError

from storyboard.db.api import base as api_base
from storyboard.db.api import users as users_api
from storyboard.db import models
from storyboard.openstack.common.gettextutils import _  # noqa


def _board_get(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.Board).options(
        subqueryload(models.Board.lanes)).filter_by(id=id)

    return query.first()


def get(id):
    return _board_get(id)


def _build_board_query(title=None, creator_id=None, user_id=None,
                       project_id=None, archived=False, current_user=None,
                       session=None, item_type=None, story_id=None,
                       task_id=None):
    query = api_base.model_query(models.Board, session=session).distinct()

    query = api_base.apply_query_filters(query=query,
                                         model=models.Board,
                                         title=title,
                                         creator_id=creator_id,
                                         project_id=project_id)

    # Filter out boards that the current user can't see
    query = api_base.filter_private_boards(query, current_user)

    # Filter by boards that a given user has permissions to use
    if user_id:
        board_permissions = aliased(models.board_permissions)
        permissions = aliased(models.Permission)
        user_permissions = aliased(models.user_permissions)
        users = aliased(models.User)
        query = query.join(
            (board_permissions,
             models.Board.id == board_permissions.c.board_id)
        )
        query = query.join(
            (permissions,
             board_permissions.c.permission_id == permissions.id)
        )
        query = query.join(
            (user_permissions,
             permissions.id == user_permissions.c.permission_id)
        )
        query = query.join((users, user_permissions.c.user_id == users.id))
        query = query.filter(users.id == user_id)

    # Filter by whether or not we want archived boards
    query = query.filter(models.Board.archived == archived)

    if story_id or task_id:
        query = query.join(models.BoardWorklist,
                           models.Worklist)

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

    return query


def get_all(title=None, creator_id=None, user_id=None, project_id=None,
            task_id=None, story_id=None, archived=False, offset=None,
            limit=None, sort_field=None, sort_dir=None, current_user=None,
            item_type=None, **kwargs):
    if sort_field is None:
        sort_field = 'id'
    if sort_dir is None:
        sort_dir = 'asc'

    boards = _build_board_query(title=title,
                                creator_id=creator_id,
                                project_id=project_id,
                                user_id=user_id,
                                archived=archived,
                                current_user=current_user,
                                item_type=item_type,
                                story_id=story_id,
                                task_id=task_id,
                                **kwargs)

    boards = api_base.paginate_query(query=boards,
                                     model=models.Board,
                                     limit=limit,
                                     offset=offset,
                                     sort_key=sort_field,
                                     sort_dir=sort_dir)
    return boards.all()


def get_count(title=None, creator_id=None, user_id=None, project_id=None,
              task_id=None, story_id=None, item_type=None, archived=False,
              current_user=None, **kwargs):
    query = _build_board_query(title=title,
                               creator_id=creator_id,
                               project_id=project_id,
                               user_id=user_id,
                               archived=archived,
                               current_user=current_user,
                               story_id=story_id,
                               task_id=task_id,
                               item_type=item_type,
                               **kwargs)
    return query.count()


def create(values):
    board = api_base.entity_create(models.Board, values)
    return board


def update(id, values):
    return api_base.entity_update(models.Board, id, values)


def add_lane(board, lane_dict):
    # Make sure we're adding the lane to the right board
    lane_dict['board_id'] = board.id

    if lane_dict.get('list_id') is None:
        raise ClientSideError(_("A lane must have a worklist_id."))

    if lane_dict.get('position') is None:
        lane_dict['position'] = len(board.lanes)

    api_base.entity_create(models.BoardWorklist, lane_dict)

    return board


def update_lane(board, lane, new_lane):
    # Make sure we aren't messing up the board ID
    new_lane['board_id'] = board.id

    if new_lane.get('list_id') is None:
        raise ClientSideError(_("A lane must have a worklist_id."))

    api_base.entity_update(models.BoardWorklist, lane.id, new_lane)


def get_from_lane(worklist):
    lanes = api_base.entity_get_all(models.BoardWorklist,
                                    list_id=worklist.id)
    if lanes:
        lane = lanes[0]
        return lane.board


# FIXME: This assumes that boards only contain a task or story once, which
#        is not actually enforced when creating a card.
def get_card(board, item_type, item_id, archived=False):
    for lane in board.lanes:
        for card in lane.worklist.items:
            if (card.item_type == item_type and
                    card.item_id == item_id and
                    card.archived == archived):
                return card


def has_card(board, item_type, item_id):
    for lane in board.lanes:
        for item in lane.worklist.items:
            if item.item_id == item_id and item.item_type == item_type:
                return True
    return False


def get_owners(board):
    for permission in board.permissions:
        if permission.codename == 'edit_board':
            return [user.id for user in permission.users]


def get_users(board):
    for permission in board.permissions:
        if permission.codename == 'move_cards':
            return [user.id for user in permission.users]


def get_permissions(board, user_id):
    user = users_api.user_get(user_id)
    if user is not None:
        return [permission.codename for permission in board.permissions
                if permission in user.permissions]
    return []


def create_permission(board_id, permission_dict, session=None):
    board = _board_get(board_id, session=session)
    users = permission_dict.pop('users')
    permission = api_base.entity_create(
        models.Permission, permission_dict, session=session)
    board.permissions.append(permission)
    for user_id in users:
        user = users_api.user_get(user_id, session=session)
        user.permissions.append(permission)
    return permission


def update_permission(board_id, permission_dict):
    board = _board_get(board_id)
    id = None
    for permission in board.permissions:
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


def visible(board, user=None):
    if not board:
        return False
    if user and board.private:
        permissions = get_permissions(board, user)
        return any(name in permissions
                   for name in ['edit_board', 'move_cards'])
    return not board.private


def editable(board, user=None):
    if not board:
        return False
    if not user:
        return False
    return 'edit_board' in get_permissions(board, user)
