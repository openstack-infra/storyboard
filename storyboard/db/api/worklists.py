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


def get_all(title=None, creator_id=None, project_id=None,
            board_id=None, sort_field=None, sort_dir=None,
            **kwargs):
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


def get_item_by_id(item_id):
    session = api_base.get_session()
    query = session.query(models.WorklistItem).filter_by(id=str(item_id))

    return query.first()


def get_item_at_position(worklist_id, list_position):
    session = api_base.get_session()
    query = session.query(models.WorklistItem).filter_by(
        list_id=worklist_id, list_position=list_position)

    return query.first()


def update_item_list_id(item, new_list_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        old_list = _worklist_get(item.list_id)
        new_list = _worklist_get(new_list_id)

        if new_list is None:
            raise exc.NotFound(_("Worklist %s not found") % new_list_id)

        old_list.items.remove(item)
        new_list.items.append(item)


def update_item(worklist_id, item_id, list_position, list_id=None):
    item = get_item_by_id(item_id)
    update_dict = {'list_position': list_position}
    if list_id is not None:
        update_item_list_id(item, list_id)
    api_base.entity_update(models.WorklistItem, item_id, update_dict)


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
