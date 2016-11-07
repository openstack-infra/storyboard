# Copyright (c) 2016 Codethink Limited
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

from datetime import datetime

from oslo_config import cfg
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import boards as boards_api
from storyboard.db.api import due_dates as due_dates_api
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import worklists as worklists_api


CONF = cfg.CONF


class PermissionsController(rest.RestController):
    """Manages operations on due date permissions."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wtypes.text], int)
    def get(self, due_date_id):
        """Get due date permissions for the current user.

        :param due_date_id: The ID of the due date.

        """
        due_date = due_dates_api.get(due_date_id)
        if due_dates_api.visible(due_date, request.current_user_id):
            return due_dates_api.get_permissions(due_date,
                                                 request.current_user_id)
        else:
            raise exc.NotFound(_("Due date %s not found") % due_date_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def post(self, due_date_id, permission):
        """Add a new permission to the due date.

        :param due_date_id: The ID of the due date.
        :param permission: The dict used to create the permission.

        """
        if due_dates_api.editable(due_dates_api.get(due_date_id),
                                  request.current_user_id):
            return due_dates_api.create_permission(due_date_id, permission)
        else:
            raise exc.NotFound(_("Due date %s not found") % due_date_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def put(self, due_date_id, permission):
        """Update a permission of the due date.

        :param due_date_id: The ID of the due date.
        :param permission: The new contents of the permission.

        """
        if due_dates_api.editable(due_dates_api.get(due_date_id),
                                  request.current_user_id):
            return due_dates_api.update_permission(
                due_date_id, permission).codename
        else:
            raise exc.NotFound(_("Due date %s not found") % due_date_id)


class DueDatesController(rest.RestController):
    """Manages operations on due dates."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.DueDate, int)
    def get_one(self, id):
        """Retrieve details about one due date.

        :param id: The ID of the due date.

        """
        due_date = due_dates_api.get(id)

        if due_dates_api.visible(due_date, request.current_user_id):
            due_date_model = wmodels.DueDate.from_db_model(due_date)
            due_date_model.resolve_items(due_date)
            due_date_model.resolve_permissions(due_date)
            return due_date_model
        else:
            return exc.NotFound(_("Due date %s not found") % id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.DueDate], wtypes.text, datetime, int, int,
                         int, int, wtypes.text, wtypes.text)
    def get_all(self, name=None, date=None, board_id=None, worklist_id=None,
                user=None, owner=None, sort_field='id', sort_dir='asc'):
        """Retrieve details about all the due dates.

        :param name: The name of the due date.
        :param date: The date of the due date.
        :param board_id: The ID of a board to filter by.
        :param worklist_id: The ID of a worklist to filter by.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).

        """
        due_dates = due_dates_api.get_all(name=name,
                                          date=date,
                                          board_id=board_id,
                                          worklist_id=worklist_id,
                                          user=user,
                                          owner=owner,
                                          sort_field=sort_field,
                                          sort_dir=sort_dir)
        visible_dates = []
        for due_date in due_dates:
            if due_dates_api.visible(due_date, request.current_user_id):
                due_date_model = wmodels.DueDate.from_db_model(due_date)
                due_date_model.resolve_items(due_date)
                due_date_model.resolve_permissions(due_date)
                visible_dates.append(due_date_model)

        response.headers['X-Total'] = str(len(visible_dates))

        return visible_dates

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.DueDate, body=wmodels.DueDate)
    def post(self, due_date):
        """Create a new due date.

        :param due_date: A due date within the request body.

        """
        due_date_dict = due_date.as_dict()
        user_id = request.current_user_id

        if due_date.creator_id and due_date.creator_id != user_id:
            abort(400, _("You can't select the creator of a due date."))
        due_date_dict.update({'creator_id': user_id})

        board_id = due_date_dict.pop('board_id')
        worklist_id = due_date_dict.pop('worklist_id')
        if 'stories' in due_date_dict:
            del due_date_dict['stories']
        if 'tasks' in due_date_dict:
            del due_date_dict['tasks']
        owners = due_date_dict.pop('owners')
        users = due_date_dict.pop('users')
        if not owners:
            owners = [user_id]
        if not users:
            users = []

        created_due_date = due_dates_api.create(due_date_dict)

        if board_id is not None:
            date = due_dates_api.get(created_due_date.id)
            date.boards.append(boards_api.get(board_id))

        if worklist_id is not None:
            date = due_dates_api.get(created_due_date.id)
            date.worklists.append(worklists_api.get(worklist_id))

        edit_permission = {
            'name': 'edit_due_date_%d' % created_due_date.id,
            'codename': 'edit_date',
            'users': owners
        }
        assign_permission = {
            'name': 'assign_due_date_%d' % created_due_date.id,
            'codename': 'assign_date',
            'users': users
        }
        due_dates_api.create_permission(created_due_date.id, edit_permission)
        due_dates_api.create_permission(created_due_date.id, assign_permission)

        created_due_date = due_dates_api.get(created_due_date.id)
        due_date_model = wmodels.DueDate.from_db_model(created_due_date)
        due_date_model.resolve_items(created_due_date)
        due_date_model.resolve_permissions(created_due_date,
                                           request.current_user_id)
        return due_date_model

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.DueDate, int, body=wmodels.DueDate)
    def put(self, id, due_date):
        """Modify a due date.

        :param id: The ID of the due date to edit.
        :param due_date: The new due date within the request body.

        """
        if not due_dates_api.assignable(due_dates_api.get(id),
                                        request.current_user_id):
            raise exc.NotFound(_("Due date %s not found") % id)

        original_due_date = due_dates_api.get(id)

        due_date_dict = due_date.as_dict(omit_unset=True)
        editing = any(prop in due_date_dict
                      for prop in ('name', 'date', 'private'))
        if editing and not due_dates_api.editable(original_due_date,
                                                  request.current_user_id):
            raise exc.NotFound(_("Due date %s not found") % id)

        if due_date.creator_id \
                and due_date.creator_id != original_due_date.creator_id:
            abort(400, _("You can't select the creator of a due date."))

        if 'tasks' in due_date_dict:
            tasks = due_date_dict.pop('tasks')
            db_tasks = []
            for task in tasks:
                db_tasks.append(tasks_api.task_get(
                    task.id, current_user=request.current_user_id))
            due_date_dict['tasks'] = db_tasks

        if 'stories' in due_date_dict:
            stories = due_date_dict.pop('stories')
            db_stories = []
            for story in stories:
                db_stories.append(stories_api.story_get_simple(
                    story.id, current_user=request.current_user_id))
            due_date_dict['stories'] = db_stories

        board = None
        worklist = None
        if 'board_id' in due_date_dict:
            board = boards_api.get(due_date_dict['board_id'])

        if 'worklist_id' in due_date_dict:
            worklist = worklists_api.get(due_date_dict['worklist_id'])

        updated_due_date = due_dates_api.update(id, due_date_dict)

        if board:
            updated_due_date.boards.append(board)

        if worklist:
            updated_due_date.worklists.append(worklist)

        if due_dates_api.visible(updated_due_date, request.current_user_id):
            due_date_model = wmodels.DueDate.from_db_model(updated_due_date)
            due_date_model.resolve_items(updated_due_date)
            due_date_model.resolve_permissions(updated_due_date,
                                               request.current_user_id)
            return due_date_model
        else:
            raise exc.NotFound(_("Due date %s not found") % id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int)
    def delete(self, id, board_id):
        """Stop associating a due date with a board.

        Note: We don't allow actual deletion of due dates.

        :param id: The ID of the due date.
        :param board_id: The ID of the board.

        """
        due_date = due_dates_api.get(id)
        if not due_dates_api.editable(due_date, request.current_user_id):
            raise exc.NotFound(_("Due date %s not found") % id)

        board = boards_api.get(board_id)
        if not boards_api.editable(board, request.current_user_id):
            raise exc.NotFound(_("Board %s not found") % board_id)

        if board in due_date.boards:
            due_date.boards.remove(board)
            for lane in board.lanes:
                for card in lane.worklist.items:
                    if card.display_due_date == due_date.id:
                        update = {'display_due_date': None}
                        worklists_api.update_item(card.id, update)

    permissions = PermissionsController()
