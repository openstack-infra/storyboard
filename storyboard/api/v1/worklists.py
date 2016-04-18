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
from storyboard.db.api import worklists as worklists_api
from storyboard.openstack.common.gettextutils import _  # noqa


CONF = cfg.CONF


class PermissionsController(rest.RestController):
    """Manages operations on worklist permissions."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wtypes.text], int)
    def get(self, worklist_id):
        """Get worklist permissions for the current user.

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)
        if worklists_api.visible(worklist, request.current_user_id):
            return worklists_api.get_permissions(worklist,
                                                 request.current_user_id)
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def post(self, worklist_id, permission):
        """Add a new permission to the worklist.

        :param worklist_id: The ID of the worklist.
        :param permission: The dict to use to create the permission.

        """
        if worklists_api.editable(worklists_api.get(worklist_id),
                                  request.current_user_id):
            return worklists_api.create_permission(worklist_id)
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def put(self, worklist_id, permission):
        """Update a permission of the worklist.

        :param worklist_id: The ID of the worklist.
        :param permission: The new contents of the permission.

        """
        if worklists_api.editable(worklists_api.get(worklist_id),
                                  request.current_user_id):
            return worklists_api.update_permission(
                worklist_id, permission).codename
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)


class FilterSubcontroller(rest.RestController):
    """Manages filters on automatic worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int, int)
    def get_one(self, worklist_id, filter_id):
        """Get a single filter for the worklist.

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklist or not worklists_api.visible(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        filter = worklists_api.get_filter(worklist, filter_id)

        return wmodels.WorklistFilter.from_db_model(filter)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.WorklistFilter], int)
    def get(self, worklist_id):
        """Get filters for an automatic worklist.

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklist or not worklists_api.visible(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        return [wmodels.WorklistFilter.from_db_model(filter)
                for filter in worklist.filters]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int,
                         body=wmodels.WorklistFilter)
    def post(self, worklist_id, filter):
        """Create a new filter for the worklist.

        :param worklist_id: The ID of the worklist to set the filter on.
        :param filter: The filter to set.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        created = worklists_api.create_filter(worklist_id, filter.as_dict())
        model = wmodels.WorklistFilter.from_db_model(created)
        model.resolve_criteria(created)
        return model

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int, int,
                         body=wmodels.WorklistFilter)
    def put(self, worklist_id, filter_id, filter):
        """Update a filter on the worklist.

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter to be updated.
        :param filter: The new contents of the filter.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        update_dict = filter.as_dict(omit_unset=True)
        updated = worklists_api.update_filter(filter_id, update_dict)

        return wmodels.WorklistFilter.from_db_model(updated)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int)
    def delete(self, worklist_id, filter_id):
        """Delete a filter from a worklist.

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter to be deleted.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        worklists_api.delete_filter(filter_id)


class ItemsSubcontroller(rest.RestController):
    """Manages operations on the items in worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.WorklistItem], int)
    def get(self, worklist_id):
        """Get items inside a worklist.

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklist or not worklists_api.visible(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        if worklist.automatic:
            return [wmodels.WorklistItem(**item)
                    for item in worklists_api.filter_items(worklist)]

        if worklist.items is None:
            return []

        worklist.items.sort(key=lambda i: i.list_position)

        return [wmodels.WorklistItem.from_db_model(item)
                for item in worklist.items]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistItem, int, int, wtypes.text, int)
    def post(self, id, item_id, item_type, list_position):
        """Add an item to a worklist.

        :param id: The ID of the worklist.
        :param item_id: The ID of the item.
        :param item_type: The type of the item (i.e. "story" or "task").
        :param list_position: The position in the list to add the item.

        """
        user_id = request.current_user_id
        if not worklists_api.editable_contents(worklists_api.get(id),
                                               user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)
        worklists_api.add_item(id, item_id, item_type, list_position)

        return wmodels.WorklistItem.from_db_model(
            worklists_api.get_item_at_position(id, list_position))

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistItem, int, int, int, int, int)
    def put(self, id, item_id, list_position, list_id=None,
            display_due_date=None):
        """Update a WorklistItem.

        This method also updates the positions of other items in affected
        worklists, if necessary.

        :param id: The ID of the worklist.
        :param item_id: The ID of the worklist_item to be moved.
        :param display_due_date: The ID of the due date displayed on the item.

        """
        user_id = request.current_user_id
        if not worklists_api.editable_contents(worklists_api.get(id),
                                               user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)
        if worklists_api.get_item_by_id(item_id) is None:
            raise exc.NotFound(_("Item %s seems to have been deleted, "
                                 "try refreshing your page.") % item_id)
        worklists_api.move_item(id, item_id, list_position, list_id)

        if display_due_date is not None:
            if display_due_date == -1:
                display_due_date = None
            update_dict = {
                'display_due_date': display_due_date
            }
            worklists_api.update_item(item_id, update_dict)

        updated = worklists_api.get_item_by_id(item_id)
        result = wmodels.WorklistItem.from_db_model(updated)
        result.resolve_due_date(updated)
        return result

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int, status_code=204)
    def delete(self, id, item_id):
        """Remove an item from a worklist.

        :param id: The ID of the worklist.
        :param item_id: The ID of the worklist item to be removed.

        """
        user_id = request.current_user_id
        if not worklists_api.editable_contents(worklists_api.get(id),
                                               user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)
        item = worklists_api.get_item_by_id(item_id)
        if item is None:
            raise exc.NotFound(_("Item %s seems to have already been deleted,"
                                 " try refreshing your page.") % item_id)
        worklists_api.update_item(item_id, {'archived': True})


class WorklistsController(rest.RestController):
    """Manages operations on worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Worklist, int)
    def get_one(self, worklist_id):
        """Retrieve details about one worklist.

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)

        user_id = request.current_user_id
        if worklist and worklists_api.visible(worklist, user_id):
            worklist_model = wmodels.Worklist.from_db_model(worklist)
            worklist_model.resolve_items(worklist)
            worklist_model.resolve_permissions(worklist)
            worklist_model.resolve_filters(worklist)
            return worklist_model
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Worklist], wtypes.text, int, int,
                         bool, int, bool, wtypes.text, wtypes.text, int)
    def get_all(self, title=None, creator_id=None, project_id=None,
                archived=False, user_id=None, hide_lanes=True,
                sort_field='id', sort_dir='asc', board_id=None):
        """Retrieve definitions of all of the worklists.

        :param title: A string to filter the title by.
        :param creator_id: Filter worklists by their creator.
        :param project_id: Filter worklists by project ID.
        :param archived: Filter worklists by whether they are archived or not.
        :param user_id: Filter worklists by the users with permissions.
        :param hide_lanes: If true, don't return worklists which are lanes in
        a board.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        :param board_id: Get all worklists in the board with this id. Other
        filters are not applied.

        """
        worklists = worklists_api.get_all(title=title,
                                          creator_id=creator_id,
                                          project_id=project_id,
                                          archived=archived,
                                          board_id=board_id,
                                          user_id=user_id,
                                          sort_field=sort_field,
                                          sort_dir=sort_dir)

        user_id = request.current_user_id
        visible_worklists = []
        for worklist in worklists:
            if (worklists_api.visible(worklist, user_id, hide_lanes) and
                worklist.archived == archived):
                worklist_model = wmodels.Worklist.from_db_model(worklist)
                worklist_model.resolve_permissions(worklist)
                worklist_model.items = [
                    wmodels.WorklistItem.from_db_model(item)
                    for item in worklist.items
                ]
                visible_worklists.append(worklist_model)

        # Apply the query response headers
        response.headers['X-Total'] = str(len(visible_worklists))

        return visible_worklists

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Worklist, body=wmodels.Worklist)
    def post(self, worklist):
        """Create a new worklist.

        :param worklist: A worklist within the request body.

        """
        worklist_dict = worklist.as_dict()
        user_id = request.current_user_id

        if worklist.creator_id and worklist.creator_id != user_id:
            abort(400, _("You can't select the creator of a worklist."))
        worklist_dict.update({"creator_id": user_id})
        if 'items' in worklist_dict:
            del worklist_dict['items']

        filters = worklist_dict.pop('filters')
        owners = worklist_dict.pop('owners')
        users = worklist_dict.pop('users')
        if not owners:
            owners = [user_id]
        if not users:
            users = []

        created_worklist = worklists_api.create(worklist_dict)

        edit_permission = {
            'name': 'edit_worklist_%d' % created_worklist.id,
            'codename': 'edit_worklist',
            'users': owners
        }
        move_permission = {
            'name': 'move_items_%d' % created_worklist.id,
            'codename': 'move_items',
            'users': users
        }
        worklists_api.create_permission(created_worklist.id, edit_permission)
        worklists_api.create_permission(created_worklist.id, move_permission)

        if worklist_dict['automatic']:
            for filter in filters:
                worklists_api.create_filter(created_worklist.id,
                                            filter.as_dict())

        return wmodels.Worklist.from_db_model(created_worklist)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Worklist, int, body=wmodels.Worklist)
    def put(self, id, worklist):
        """Modify this worklist.

        :param id: The ID of the worklist.
        :param worklist: A worklist within the request body.

        """
        user_id = request.current_user_id
        if not worklists_api.editable(worklists_api.get(id), user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)

        # We don't use this endpoint to update the worklist's contents
        if worklist.items != wtypes.Unset:
            del worklist.items

        # We don't use this endpoint to update the worklist's filters either
        if worklist.filters != wtypes.Unset:
            del worklist.filters

        worklist_dict = worklist.as_dict(omit_unset=True)

        updated_worklist = worklists_api.update(id, worklist_dict)

        if worklists_api.visible(updated_worklist, user_id):
            worklist_model = wmodels.Worklist.from_db_model(updated_worklist)
            worklist_model.resolve_items(updated_worklist)
            worklist_model.resolve_permissions(updated_worklist)
            return worklist_model
        else:
            raise exc.NotFound(_("Worklist %s not found"))

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, worklist_id):
        """Archive this worklist.

        :param worklist_id: The ID of the worklist to be archived.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        worklists_api.update(worklist_id, {"archived": True})

    items = ItemsSubcontroller()
    permissions = PermissionsController()
    filters = FilterSubcontroller()
