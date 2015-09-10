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


def get_all(title=None, creator_id=None, project_id=None,
            sort_field=None, sort_dir=None, **kwargs):
    return api_base.entity_get_all(models.Board,
                                   title=title,
                                   creator_id=creator_id,
                                   project_id=project_id,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def create(values):
    board = api_base.entity_create(models.Board, values)
    return board


def update(id, values):
    return api_base.entity_update(models.Board, id, values)


def add_lane(board_id, lane_dict):
    board = _board_get(board_id)
    if board is None:
        raise exc.NotFound(_("Board %s not found") % board_id)

    # Make sure we're adding the lane to the right board
    lane_dict['board_id'] = board_id

    if lane_dict.get('list_id') is None:
        raise ClientSideError(_("A lane must have a worklist_id."))

    if lane_dict.get('position') is None:
        lane_dict['position'] = len(board.lanes)

    api_base.entity_create(models.BoardWorklist, lane_dict)

    return board


def update_lane(board_id, lane, new_lane):
    # Make sure we aren't messing up the board ID
    new_lane['board_id'] = board_id

    if new_lane.get('list_id') is None:
        raise ClientSideError(_("A lane must have a worklist_id."))

    api_base.entity_update(models.BoardWorklist, lane.id, new_lane)
