# Copyright (c) 2016 Codethink Limited
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

from sqlalchemy import func
from wsme.exc import ClientSideError

from storyboard._i18n import _
from storyboard.db.api import base as api_base
from storyboard.db.api import users as users_api
from storyboard.db import models


def _due_date_get(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.DueDate).filter_by(id=id)

    return query.first()


def _due_date_build_query(name=None, date=None, board_id=None,
                          worklist_id=None, user=None, owner=None):
    query = api_base.model_query(models.DueDate)

    query = api_base.apply_query_filters(query=query,
                                         model=models.DueDate,
                                         name=name,
                                         date=date)

    if board_id:
        query = query.join(models.board_due_dates,
                           models.Board)
        query = query.filter(models.Board.id == board_id)

    if worklist_id:
        query = query.join(models.worklist_due_dates,
                           models.Worklist)
        query = query.filter(models.Worklist.id == worklist_id)

    if user and not owner:
        query = query.join(models.due_date_permissions,
                           models.Permission,
                           models.user_permissions,
                           models.User)
        query = query.filter(models.User.id == user)

    if owner and not user:
        query = query.join(models.due_date_permissions,
                           models.Permission,
                           models.user_permissions,
                           models.User)
        query = query.filter(models.Permission.codename == 'edit_date',
                             models.User.id == owner)

    if owner and user:
        query = query.join(models.due_date_permissions,
                           models.Permission,
                           models.user_permissions,
                           models.User)
        user_dates = query.filter(models.User.id == user)
        owner_dates = query.filter(models.Permission.codename == 'edit_date',
                                   models.User.id == owner)
        query = user_dates.union(owner_dates)
        query = query.group_by(models.DueDate.id)
        query = query.having(func.count(models.DueDate.id) >= 2)

    return query


def get(id):
    return _due_date_get(id)


def get_all(name=None, date=None, board_id=None, worklist_id=None,
            user=None, owner=None, sort_field=None, sort_dir=None, **kwargs):
    query = _due_date_build_query(name=name,
                                  date=date,
                                  board_id=board_id,
                                  worklist_id=worklist_id,
                                  user=user,
                                  owner=owner)
    query = api_base.paginate_query(query=query,
                                    model=models.DueDate,
                                    limit=None,
                                    offset=None,
                                    marker=None,
                                    sort_key=sort_field,
                                    sort_dir=sort_dir)
    return query.all()


def create(values):
    return api_base.entity_create(models.DueDate, values)


def update(id, values):
    return api_base.entity_update(models.DueDate, id, values)


def get_visible_items(due_date, current_user=None):
    stories = api_base.filter_private_stories(due_date.stories, current_user)
    tasks = due_date.tasks.outerjoin(models.Story)
    tasks = api_base.filter_private_stories(tasks, current_user)

    return stories, tasks


def get_owners(due_date):
    for permission in due_date.permissions:
        if permission.codename == 'edit_date':
            return [user.id for user in permission.users]


def get_users(due_date):
    for permission in due_date.permissions:
        if permission.codename == 'assign_date':
            return [user.id for user in permission.users]


def get_permissions(due_date, user_id):
    user = users_api.user_get(user_id)
    if user is not None:
        return [permission.codename for permission in due_date.permissions
                if permission in user.permissions]
    return []


def create_permission(due_date_id, permission_dict, session=None):
    due_date = _due_date_get(due_date_id, session=session)
    users = permission_dict.pop('users')
    permission = api_base.entity_create(
        models.Permission, permission_dict, session=session)
    due_date.permissions.append(permission)
    for user_id in users:
        user = users_api.user_get(user_id, session=session)
        user.permissions.append(permission)
    return permission


def update_permission(due_date_id, permission_dict):
    due_date = _due_date_get(due_date_id)
    id = None
    for permission in due_date.permissions:
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


def visible(due_date, user=None):
    if not due_date:
        return False
    if user and due_date.private:
        permissions = get_permissions(due_date, user)
        return any(name in permissions
                   for name in ['edit_date', 'assign_date'])
    return not due_date.private


def assignable(due_date, user=None):
    if not due_date or not user:
        return False
    permissions = get_permissions(due_date, user)
    return any(name in permissions for name in ('edit_date', 'assign_date'))


def editable(due_date, user=None):
    if not due_date:
        return False
    if not user:
        return False
    return 'edit_date' in get_permissions(due_date, user)
