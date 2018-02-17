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

import copy

from oslo_config import cfg
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
import six
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import boards as boards_api
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api
from storyboard.db.api import users as users_api
from storyboard.db.api import worklists as worklists_api


CONF = cfg.CONF


def serialize_lane(lane):
    return {
        "worklist_id": lane.list_id,
        "position": lane.position
    }


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
                del new_lane.worklist
                original = copy.deepcopy(lane)
                boards_api.update_lane(
                    board, lane, new_lane.as_dict(omit_unset=True))
                updated = {
                    "old": serialize_lane(original),
                    "new": serialize_lane(new_lane)
                }

                events_api.board_lanes_changed_event(board_id,
                                                     request.current_user_id,
                                                     updated=updated)

    for lane in board_dict['lanes']:
        if lane.list_id not in existing_list_ids:
            lane.worklist = None
            boards_api.add_lane(board, lane.as_dict(omit_unset=True))
            events_api.board_lanes_changed_event(board_id,
                                                 request.current_user_id,
                                                 added=serialize_lane(lane))

    board = boards_api.get(board_id)
    del board_dict['lanes']


def post_timeline_events(original, updated):
    author_id = request.current_user_id

    if original.title != updated.title:
        events_api.board_details_changed_event(
            original.id,
            author_id,
            'title',
            original.title,
            updated.title)

    if original.description != updated.description:
        events_api.board_details_changed_event(
            original.id,
            author_id,
            'description',
            original.description,
            updated.description)

    if original.private != updated.private:
        events_api.board_details_changed_event(
            original.id,
            author_id,
            'private',
            original.private,
            updated.private)

    if original.archived != updated.archived:
        events_api.board_details_changed_event(
            original.id,
            author_id,
            'archived',
            original.archived,
            updated.archived)


class PermissionsController(rest.RestController):
    """Manages operations on board permissions."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wtypes.text], int)
    def get(self, board_id):
        """Get board permissions for the current user.

        :param board_id: The ID of the board.

        """
        board = boards_api.get(board_id)
        if boards_api.visible(board, request.current_user_id):
            return boards_api.get_permissions(board, request.current_user_id)
        else:
            raise exc.NotFound(_("Board %s not found") % board_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def post(self, board_id, permission):
        """Add a new permission to the board.

        :param board_id: The ID of the board.
        :param permission: The dict to use to create the permission.

        """
        user_id = request.current_user_id
        if boards_api.editable(boards_api.get(board_id), user_id):
            created = boards_api.create_permission(board_id, permission)

            users = [{user.id: user.full_name} for user in created.users]
            events_api.board_permission_created_event(board_id,
                                                      user_id,
                                                      created.id,
                                                      created.codename,
                                                      users)

            return created
        else:
            raise exc.NotFound(_("Board %s not found") % board_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def put(self, board_id, permission):
        """Update a permission of the board.

        :param board_id: The ID of the board.
        :param permission: The new contents of the permission.

        """
        user_id = request.current_user_id
        board = boards_api.get(board_id)

        old = None
        for perm in board.permissions:
            if perm.codename == permission['codename']:
                old = perm

        if old is None:
            raise exc.NotFound(_("Permission with codename %s not found")
                               % permission['codename'])

        old_users = {user.id: user.full_name for user in old.users}

        if boards_api.editable(board, user_id):
            updated = boards_api.update_permission(board_id, permission)
            new_users = {user.id: user.full_name for user in updated.users}

            added = [{id: name} for id, name in six.iteritems(new_users)
                     if id not in old_users]
            removed = [{id: name} for id, name in six.iteritems(old_users)
                       if id not in new_users]

            if added or removed:
                events_api.board_permissions_changed_event(board.id,
                                                           user_id,
                                                           updated.id,
                                                           updated.codename,
                                                           added,
                                                           removed)
        else:
            raise exc.NotFound(_("Board %s not found") % board_id)


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
        story_cache = {story.id: story for story in stories_api.story_get_all(
                       board_id=id, current_user=user_id)}
        task_cache = {task.id: task for task in tasks_api.task_get_all(
                      board_id=id, current_user=user_id)}
        if boards_api.visible(board, user_id):
            board_model = wmodels.Board.from_db_model(board)
            board_model.resolve_lanes(board, story_cache, task_cache)
            board_model.resolve_due_dates(board)
            board_model.resolve_permissions(board)
            return board_model
        else:
            raise exc.NotFound(_("Board %s not found") % id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Board], wtypes.text, int, int, bool,
                         int, int, int, wtypes.text, int, int, wtypes.text,
                         wtypes.text)
    def get_all(self, title=None, creator_id=None, project_id=None,
                archived=False, user_id=None, story_id=None, task_id=None,
                item_type=None, offset=None, limit=None, sort_field='id',
                sort_dir='asc'):
        """Retrieve definitions of all of the boards.

        :param title: A string to filter the title by.
        :param creator_id: Filter boards by their creator.
        :param project_id: Filter boards by project ID.
        :param archived: Filter boards by whether they are archived or not.
        :param story_id: Filter boards by whether they contain a story.
        :param task_id: Filter boards by whether they contain a task.
        :param item_type: Used when filtering by story_id. If
                          item_type is 'story' then only return
                          worklists that contain the story, if
                          item_type is 'task' then only return
                          worklists that contain tasks from the story,
                          otherwise return worklists that contain the
                          story or tasks from the story.
        :param offset: Value to offset results by.
        :param limit: Maximum number of results to return.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).

        """
        current_user = request.current_user_id
        boards = boards_api.get_all(title=title,
                                    creator_id=creator_id,
                                    user_id=user_id,
                                    project_id=project_id,
                                    story_id=story_id,
                                    task_id=task_id,
                                    item_type=item_type,
                                    offset=offset,
                                    limit=limit,
                                    current_user=current_user,
                                    sort_field=sort_field,
                                    sort_dir=sort_dir)
        count = boards_api.get_count(title=title,
                                     creator_id=creator_id,
                                     user_id=user_id,
                                     project_id=project_id,
                                     story_id=story_id,
                                     task_id=task_id,
                                     item_type=item_type,
                                     current_user=current_user,)

        visible_boards = []
        for board in boards:
            board_model = wmodels.Board.from_db_model(board)
            board_model.resolve_lanes(board, resolve_items=False)
            board_model.resolve_permissions(board)
            visible_boards.append(board_model)

        # Apply the query response headers
        response.headers['X-Total'] = str(count)
        if limit is not None:
            response.headers['X-Limit'] = str(limit)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

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
        lanes = board_dict.pop('lanes') or []
        owners = board_dict.pop('owners')
        users = board_dict.pop('users')
        if not owners:
            owners = [user_id]
        if not users:
            users = []

        # We can't set due dates when creating boards at the moment.
        if 'due_dates' in board_dict:
            del board_dict['due_dates']

        created_board = boards_api.create(board_dict)
        events_api.board_created_event(created_board.id,
                                       user_id,
                                       created_board.title,
                                       created_board.description)
        for lane in lanes:
            boards_api.add_lane(created_board, lane.as_dict())
            events_api.board_lanes_changed_event(created_board.id,
                                                 user_id,
                                                 added=serialize_lane(lane))

        edit_permission = {
            'name': 'edit_board_%d' % created_board.id,
            'codename': 'edit_board',
            'users': owners
        }
        move_permission = {
            'name': 'move_cards_%d' % created_board.id,
            'codename': 'move_cards',
            'users': users
        }
        edit = boards_api.create_permission(created_board.id, edit_permission)
        move = boards_api.create_permission(created_board.id, move_permission)
        event_owners = [{id: users_api.user_get(id).full_name}
                        for id in owners]
        event_users = [{id: users_api.user_get(id).full_name}
                       for id in users]
        events_api.board_permission_created_event(created_board.id,
                                                  user_id,
                                                  edit.id,
                                                  edit.codename,
                                                  event_owners)
        events_api.board_permission_created_event(created_board.id,
                                                  user_id,
                                                  move.id,
                                                  move.codename,
                                                  event_users)

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
        original = boards_api.get(id)
        if not boards_api.editable(original, user_id):
            raise exc.NotFound(_("Board %s not found") % id)

        story_cache = {story.id: story for story in stories_api.story_get_all(
                       board_id=id, current_user=user_id)}
        task_cache = {task.id: task for task in tasks_api.task_get_all(
                      board_id=id, current_user=user_id)}

        # We use copy here because we only need to check changes
        # to the related objects, just the board's own attributes.
        # Also, deepcopy trips up on the lanes' backrefs.
        original = copy.copy(original)

        board_dict = board.as_dict(omit_unset=True)
        update_lanes(board_dict, id)

        # This is not how we add due dates.
        if 'due_dates' in board_dict:
            del board_dict['due_dates']

        updated_board = boards_api.update(id, board_dict)

        post_timeline_events(original, updated_board)

        if boards_api.visible(updated_board, user_id):
            board_model = wmodels.Board.from_db_model(updated_board)
            board_model.resolve_lanes(updated_board, story_cache, task_cache)
            board_model.resolve_permissions(updated_board)
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
        if not boards_api.editable(board, user_id):
            raise exc.NotFound(_("Board %s not found") % id)

        # We use copy here because we only need to check changes
        # to the related objects, just the board's own attributes.
        # Also, deepcopy trips up on the lanes' backrefs.
        original = copy.copy(board)
        updated = boards_api.update(id, {"archived": True})

        post_timeline_events(original, updated)

        for lane in board.lanes:
            original = copy.deepcopy(worklists_api.get(lane.worklist.id))
            worklists_api.update(lane.worklist.id, {"archived": True})

            if not original.archived:
                events_api.worklist_details_changed_event(
                    lane.worklist.id, user_id, 'archived', original.archived,
                    True)

    permissions = PermissionsController()
