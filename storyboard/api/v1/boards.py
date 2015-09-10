# Copyright (c) 2015 Codethink Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg
from pecan import abort
from pecan import expose
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import boards as boards_api
from storyboard.db.api import worklists as worklists_api
from storyboard.openstack.common.gettextutils import _  # noqa


CONF = cfg.CONF


def visible(board, user=None):
    if not board:
        return False
    if user and board.private:
        # TODO(SotK): Permissions
        return user == board.creator_id
    return not board.private


def editable(board, user=None):
    if not board:
        return False
    if not user:
        return False
    # TODO(SotK): Permissions
    return user == board.creator_id


def get_lane(list_id, board):
    for lane in board['lanes']:
        if lane.list_id == list_id:
            return lane


def update_lanes(board_dict, board_id):
    if 'lanes' not in board_dict:
        return
    board = boards_api.get(board_id)
    new_list_ids = [lane.list_id for lane in board_dict['lanes']]
    existing_list_ids = [lane.list_id for lane in board.lanes]
    for lane in board.lanes:
        if lane.list_id in new_list_ids:
            new_lane = get_lane(lane.list_id, board_dict)
            if lane.position != new_lane.position:
                boards_api.update_lane(
                    board_id, lane, new_lane.as_dict(omit_unset=True))
    for lane in board_dict['lanes']:
        if lane.list_id not in existing_list_ids:
            boards_api.add_lane(board_id, lane.as_dict(omit_unset=True))

    board = boards_api.get(board_id)
    del board_dict['lanes']


class BoardsController(rest.RestController):
    """Manages operations on boards."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Board, int)
    def get_one(self, id):
        """Retrieve details about one board.

        :param id: The ID of the board.

        """
        board = boards_api.get(id)

        user_id = request.current_user_id
        if visible(board, user_id):
            board_model = wmodels.Board.from_db_model(board)
            board_model.lanes = [wmodels.Lane.from_db_model(lane)
                                 for lane in board.lanes]
            return board_model
        else:
            raise exc.NotFound(_("Board %s not found") % id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Board], wtypes.text, int, int,
                         bool, wtypes.text, wtypes.text)
    def get_all(self, title=None, creator_id=None, project_id=None,
                archived=False, sort_field='id', sort_dir='asc'):
        """Retrieve definitions of all of the boards.

        :param title: A string to filter the title by.
        :param creator_id: Filter boards by their creator.
        :param project_id: Filter boards by project ID.
        :param archived: Filter boards by whether they are archived or not.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).

        """
        boards = boards_api.get_all(title=title,
                                    creator_id=creator_id,
                                    project_id=project_id,
                                    sort_field=sort_field,
                                    sort_dir=sort_dir)

        visible_boards = []
        user_id = request.current_user_id
        for board in boards:
            if visible(board, user_id) and board.archived == archived:
                board_model = wmodels.Board.from_db_model(board)
                board_model.lanes = [wmodels.Lane.from_db_model(lane)
                                     for lane in board.lanes]
                visible_boards.append(board_model)

        # Apply the query response headers
        response.headers['X-Total'] = str(len(visible_boards))

        return visible_boards

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Board, body=wmodels.Board)
    def post(self, board):
        """Create a new board.

        :param board: A board within the request body.

        """
        board_dict = board.as_dict()
        user_id = request.current_user_id

        if board.creator_id and board.creator_id != user_id:
            abort(400, _("You can't select the creator of a board."))
        board_dict.update({"creator_id": user_id})
        lanes = board_dict.pop('lanes')

        created_board = boards_api.create(board_dict)
        for lane in lanes:
            boards_api.add_lane(created_board.id, lane.as_dict())

        return wmodels.Board.from_db_model(created_board)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Board, int, body=wmodels.Board)
    def put(self, id, board):
        """Modify this board.

        :param id: The ID of the board.
        :param board: The new board within the request body.

        """
        user_id = request.current_user_id
        if not editable(boards_api.get(id), user_id):
            raise exc.NotFound(_("Board %s not found") % id)

        board_dict = board.as_dict(omit_unset=True)
        update_lanes(board_dict, id)
        boards_api.update(id, board_dict)

        if visible(board, user_id):
            board_model = wmodels.Board.from_db_model(board)
            if board.lanes:
                board_model.lanes = [wmodels.Lane.from_db_model(lane)
                                     for lane in board.lanes]
            return board_model
        else:
            raise exc.NotFound(_("Board %s not found") % id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, id):
        """Archive this board.

        :param id: The ID of the board to be archived.

        """
        board = boards_api.get(id)
        user_id = request.current_user_id
        if not editable(board, user_id):
            raise exc.NotFound(_("Board %s not found") % id)

        board_dict = wmodels.Board.from_db_model(board).as_dict(
            omit_unset=True)
        board_dict['lanes'] = board.lanes
        board_dict.update({"archived": True})
        boards_api.update(id, board_dict)

        for lane in board_dict['lanes']:
            worklist = lane.worklist
            worklist_dict = wmodels.Worklist.from_db_model(worklist).as_dict(
                omit_unset=True)
            worklist_dict.update({'archived': True})
            worklists_api.update(worklist.id, worklist_dict)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wtypes.DictType(str, bool), int)
    def permissions(self, id):
        """Get the permissions the current user has for the board.

        :param id: The ID of the board to check permissions for.

        """
        board = boards_api.get(id)
        user_id = request.current_user_id
        return {
            'edit_board': editable(board, user_id),
            'move_cards': editable(board, user_id)  # TODO(SotK): check lanes
        }

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) > 1:
            if args[1] == "permissions":
                # Request to a permissions endpoint
                return self.permissions, [args[0]]

        return super(BoardsController, self)._route(args, request)
