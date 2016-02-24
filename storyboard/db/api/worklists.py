# Copyright (c) 2015 Codethink Limited
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

from sqlalchemy.orm import subqueryload
from wsme.exc import ClientSideError

from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import boards
from storyboard.db.api import stories
from storyboard.db.api import tasks
from storyboard.db.api import users as users_api
from storyboard.db import models
from storyboard.openstack.common.gettextutils import _  # noqa


def _worklist_get(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.Worklist).options(
        subqueryload(models.Worklist.items)).filter_by(id=id)

    return query.first()


def get(worklist_id):
    return _worklist_get(worklist_id)


def get_all(title=None, creator_id=None, project_id=None, board_id=None,
            user_id=None, sort_field=None, sort_dir=None, **kwargs):
    if user_id is not None:
        user = users_api.user_get(user_id)
        worklists = []
        for worklist in get_all():
            if any(permission in worklist.permissions
                   for permission in user.permissions):
                worklists.append(worklist)
        return worklists

    if board_id is not None:
        board = boards.get(board_id)
        return [lane.worklist for lane in board.lanes]

    return api_base.entity_get_all(models.Worklist,
                                   title=title,
                                   creator_id=creator_id,
                                   project_id=project_id,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def get_count(**kwargs):
    return api_base.entity_get_count(models.Worklist, **kwargs)


def create(values):
    return api_base.entity_create(models.Worklist, values)


def update(worklist_id, values):
    return api_base.entity_update(models.Worklist, worklist_id, values)


def add_item(worklist_id, item_id, item_type, list_position):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        worklist = _worklist_get(worklist_id, session)
        if worklist is None:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        if item_type == 'story':
            item = stories.story_get(item_id)
        elif item_type == 'task':
            item = tasks.task_get(item_id)
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
        session.add(worklist_item)
        session.add(worklist)

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
            old_list.items.sort(key=lambda x: x.list_position)
            modified = old_list.items[old_pos:]
            for list_item in modified:
                list_item.list_position -= 1

            new_list.items.sort(key=lambda x: x.list_position)
            modified = new_list.items[list_position:]
            for list_item in modified:
                list_item.list_position += 1
            new_list.items.append(item)
        else:
            # Item has changed position in the list.
            # Update the position of every item between the original
            # position and the final position.
            old_list.items.sort(key=lambda x: x.list_position)
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


def update_item(item_id, display_due_date):
    if display_due_date == -1:
        display_due_date = None
    updated = {
        'display_due_date': display_due_date
    }
    return api_base.entity_update(models.WorklistItem, item_id, updated)


def remove_item(worklist_id, item_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        worklist = _worklist_get(worklist_id, session)
        if worklist is None:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        item = get_item_by_id(item_id)
        if item is None:
            raise exc.NotFound(_("WorklistItem %s not found") % item_id)

        item_entry = [i for i in worklist.items if i.id == item_id][0]
        worklist.items.remove(item_entry)

        session.add(worklist)
        session.delete(item)

    return worklist


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
