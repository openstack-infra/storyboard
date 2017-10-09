# Copyright (c) 2015-2016 Codethink Limited
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
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api
from storyboard.db.api import users as users_api
from storyboard.db.api import worklists as worklists_api
from storyboard.db import models


CONF = cfg.CONF


def serialize_filter(filter):
    serialized = {
        "id": filter.id,
        "type": filter.type,
        "criteria": []
    }
    for criterion in filter.criteria:
        serialized['criteria'].append({
            "title": criterion.title,
            "negative": criterion.negative,
            "value": criterion.value,
            "field": criterion.field
        })
    return serialized


def post_timeline_events(original, updated):
    author_id = request.current_user_id

    if original.title != updated.title:
        events_api.worklist_details_changed_event(
            original.id,
            author_id,
            'title',
            original.title,
            updated.title)

    if original.private != updated.private:
        events_api.worklist_details_changed_event(
            original.id,
            author_id,
            'private',
            original.private,
            updated.private)

    if original.automatic != updated.automatic:
        events_api.worklist_details_changed_event(
            original.id,
            author_id,
            'automatic',
            original.automatic,
            updated.automatic)

    if original.archived != updated.archived:
        events_api.worklist_details_changed_event(
            original.id,
            author_id,
            'archived',
            original.archived,
            updated.archived)


class PermissionsController(rest.RestController):
    """Manages operations on worklist permissions."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wtypes.text], int)
    def get(self, worklist_id):
        """Get worklist permissions for the current user.

        Example::

          curl https://my.example.org/api/v1/worklists/31/permissions \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

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

        Example::

          TODO

        :param worklist_id: The ID of the worklist.
        :param permission: The dict to use to create the permission.

        """
        user_id = request.current_user_id
        if worklists_api.editable(worklists_api.get(worklist_id), user_id):
            created = worklists_api.create_permission(worklist_id, permission)

            users = [{user.id: user.full_name} for user in created.users]
            events_api.worklist_permission_created_event(worklist_id,
                                                         user_id,
                                                         created.id,
                                                         created.codename,
                                                         users)

            return created.codename
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.text, int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def put(self, worklist_id, permission):
        """Update a permission of the worklist.

        Example::

          TODO

        This takes a dict in the form::

            {
                "codename": "my-permission",
                "users": [
                    1,
                    2,
                    3
                ]
            }

        The given codename must match an existing permission's
        codename.

        :param worklist_id: The ID of the worklist.
        :param permission: The new contents of the permission.

        """
        user_id = request.current_user_id
        worklist = worklists_api.get(worklist_id)

        old = None
        for perm in worklist.permissions:
            if perm.codename == permission['codename']:
                old = perm

        if old is None:
            raise exc.NotFound(_("Permission with codename %s not found")
                               % permission['codename'])

        old_users = {user.id: user.full_name for user in old.users}

        if worklists_api.editable(worklist, user_id):
            updated = worklists_api.update_permission(
                worklist_id, permission)
            new_users = {user.id: user.full_name for user in updated.users}

            added = [{id: name} for id, name in six.iteritems(new_users)
                     if id not in old_users]
            removed = [{id: name} for id, name in six.iteritems(old_users)
                       if id not in new_users]

            if added or removed:
                events_api.worklist_permissions_changed_event(
                    worklist_id,
                    user_id,
                    updated.id,
                    updated.codename,
                    added,
                    removed)
            return updated.codename

        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)


class FilterSubcontroller(rest.RestController):
    """Manages filters on automatic worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int, int)
    def get_one(self, worklist_id, filter_id):
        """Get a single filter for the worklist.

        Example::

          curl https://my.example.org/api/v1/worklists/49/filters/20

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklist or not worklists_api.visible(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        filter = worklists_api.get_filter(filter_id)
        wmodel = wmodels.WorklistFilter.from_db_model(filter)
        wmodel.resolve_criteria(filter)

        return wmodel

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.WorklistFilter], int)
    def get(self, worklist_id):
        """Get filters for an automatic worklist.

        Example::

          curl https://my.example.org/api/v1/worklists/49/filters

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklist or not worklists_api.visible(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        resolved = []
        for filter in worklist.filters:
            wmodel = wmodels.WorklistFilter.from_db_model(filter)
            wmodel.resolve_criteria(filter)
            resolved.append(wmodel)

        return resolved

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int,
                         body=wmodels.WorklistFilter)
    def post(self, worklist_id, filter):
        """Create a new filter for the worklist.

        Example::

          TODO

        :param worklist_id: The ID of the worklist to set the filter on.
        :param filter: The filter to set.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        created = worklists_api.create_filter(worklist_id, filter.as_dict())

        added = serialize_filter(created)
        events_api.worklist_filters_changed_event(worklist_id,
                                                  user_id,
                                                  added=added)

        model = wmodels.WorklistFilter.from_db_model(created)
        model.resolve_criteria(created)
        return model

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistFilter, int, int,
                         body=wmodels.WorklistFilter)
    def put(self, worklist_id, filter_id, filter):
        """Update a filter on the worklist.

        Example::

          TODO

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter to be updated.
        :param filter: The new contents of the filter.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        old = serialize_filter(worklists_api.get_filter(filter_id))

        update_dict = filter.as_dict(omit_unset=True)
        updated = worklists_api.update_filter(filter_id, update_dict)

        changes = {
            "old": old,
            "new": serialize_filter(updated)
        }
        events_api.worklist_filters_changed_event(worklist_id,
                                                  user_id,
                                                  updated=changes)

        updated_model = wmodels.WorklistFilter.from_db_model(updated)
        updated_model.resolve_criteria(updated)

        return updated_model

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int)
    def delete(self, worklist_id, filter_id):
        """Delete a filter from a worklist.

        Example::

          TODO

        :param worklist_id: The ID of the worklist.
        :param filter_id: The ID of the filter to be deleted.

        """
        worklist = worklists_api.get(worklist_id)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        filter = serialize_filter(worklists_api.get_filter(filter_id))

        events_api.worklist_filters_changed_event(worklist_id,
                                                  user_id,
                                                  removed=filter)

        worklists_api.delete_filter(filter_id)


class ItemsSubcontroller(rest.RestController):
    """Manages operations on the items in worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.WorklistItem], int)
    def get(self, worklist_id):
        """Get items inside a worklist.

        Example::

          curl https://my.example.org/api/v1/worklists/49/items

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

        worklist.items.order_by(models.WorklistItem.list_position)

        visible_items = worklists_api.get_visible_items(
            worklist, current_user=request.current_user_id)
        return [
            wmodels.WorklistItem.from_db_model(item)
            for item in visible_items
        ]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistItem, int, int, wtypes.text, int)
    def post(self, id, item_id, item_type, list_position):
        """Add an item to a worklist.

        Example::

          TODO

        :param id: The ID of the worklist.
        :param item_id: The ID of the item.
        :param item_type: The type of the item (i.e. "story" or "task").
        :param list_position: The position in the list to add the item.

        """
        user_id = request.current_user_id
        if not worklists_api.editable_contents(worklists_api.get(id),
                                               user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)
        item = None
        if item_type == 'story':
            item = stories_api.story_get(
                item_id, current_user=request.current_user_id)
        elif item_type == 'task':
            item = tasks_api.task_get(
                item_id, current_user=request.current_user_id)
        if item is None:
            raise exc.NotFound(_("Item %s refers to a non-existent task or "
                                 "story.") % item_id)

        worklists_api.add_item(
            id, item_id, item_type, list_position,
            current_user=request.current_user_id)

        added = {
            "worklist_id": id,
            "item_id": item_id,
            "item_title": item.title,
            "item_type": item_type,
            "position": list_position
        }

        events_api.worklist_contents_changed_event(id, user_id, added=added)

        return wmodels.WorklistItem.from_db_model(
            worklists_api.get_item_at_position(id, list_position))

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.WorklistItem, int, int, int, int, int)
    def put(self, id, item_id, list_position, list_id=None,
            display_due_date=None):
        """Update a WorklistItem.

        Example::

          TODO

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
        card = worklists_api.get_item_by_id(item_id)
        if card is None:
            raise exc.NotFound(_("Item %s seems to have been deleted, "
                                 "try refreshing your page.") % item_id)

        item = None
        if card.item_type == 'story':
            item = stories_api.story_get(
                card.item_id, current_user=request.current_user_id)
        elif card.item_type == 'task':
            item = tasks_api.task_get(
                card.item_id, current_user=request.current_user_id)

        if item is None:
            raise exc.NotFound(_("Item %s refers to a non-existent task or "
                                 "story.") % item_id)

        old = {
            "worklist_id": card.list_id,
            "item_id": card.item_id,
            "item_title": item.title,
            "item_type": card.item_type,
            "position": card.list_position,
            "due_date_id": card.display_due_date
        }

        new = {
            "item_id": card.item_id,
            "item_title": item.title,
            "item_type": card.item_type
        }

        if list_position != card.list_position and list_position is not None:
            new['position'] = list_position
        if list_id != card.list_id and list_id is not None:
            new['worklist_id'] = list_id

        worklists_api.move_item(id, item_id, list_position, list_id)

        if display_due_date is not None:
            if display_due_date == -1:
                display_due_date = None
            update_dict = {
                'display_due_date': display_due_date
            }
            worklists_api.update_item(item_id, update_dict)
            new['due_date_id'] = display_due_date

        updated = {
            "old": old,
            "new": new
        }
        events_api.worklist_contents_changed_event(id,
                                                   user_id,
                                                   updated=updated)

        updated = worklists_api.get_item_by_id(item_id)
        result = wmodels.WorklistItem.from_db_model(updated)
        result.resolve_due_date(updated)
        return result

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int, status_code=204)
    def delete(self, id, item_id):
        """Remove an item from a worklist.

        Example::

          TODO

        :param id: The ID of the worklist.
        :param item_id: The ID of the worklist item to be removed.

        """
        user_id = request.current_user_id
        worklist = worklists_api.get(id)
        if not worklists_api.editable_contents(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)
        card = worklists_api.get_item_by_id(item_id)
        if card is None:
            raise exc.NotFound(_("Item %s seems to have already been deleted,"
                                 " try refreshing your page.") % item_id)
        worklists_api.update_item(item_id, {'archived': True})
        worklists_api.normalize_positions(worklist)

        item = None
        if card.item_type == 'story':
            item = stories_api.story_get(
                card.item_id, current_user=user_id)
        elif card.item_type == 'task':
            item = tasks_api.task_get(
                card.item_id, current_user=user_id)
        if item is None:
            item.title = ''

        removed = {
            "worklist_id": id,
            "item_id": card.item_id,
            "item_type": card.item_type,
            "item_title": item.title
        }
        events_api.worklist_contents_changed_event(id,
                                                   user_id,
                                                   removed=removed)


class WorklistsController(rest.RestController):
    """Manages operations on worklists."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Worklist, int)
    def get_one(self, worklist_id):
        """Retrieve details about one worklist.

        Example::

          curl https://my.example.org/api/v1/worklists/27

        :param worklist_id: The ID of the worklist.

        """
        worklist = worklists_api.get(worklist_id)

        user_id = request.current_user_id
        story_cache = {story.id: story for story in stories_api.story_get_all(
                       worklist_id=worklist_id, current_user=user_id)}
        task_cache = {task.id: task for task in tasks_api.task_get_all(
                      worklist_id=worklist_id, current_user=user_id)}
        if worklist and worklists_api.visible(worklist, user_id):
            worklist_model = wmodels.Worklist.from_db_model(worklist)
            worklist_model.resolve_items(worklist, story_cache, task_cache)
            worklist_model.resolve_permissions(worklist)
            worklist_model.resolve_filters(worklist)
            return worklist_model
        else:
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Worklist], wtypes.text, int, int,
                         bool, int, int, int, bool, wtypes.text, wtypes.text,
                         wtypes.text, int, int, int, int)
    def get_all(self, title=None, creator_id=None, project_id=None,
                archived=False, user_id=None, story_id=None, task_id=None,
                hide_lanes=True, sort_field='id', sort_dir='asc',
                item_type=None, board_id=None, subscriber_id=None,
                offset=None, limit=None):
        """Retrieve definitions of all of the worklists.

        Example::

          curl https://my.example.org/api/v1/worklists

        :param title: A string to filter the title by.
        :param creator_id: Filter worklists by their creator.
        :param project_id: Filter worklists by project ID.
        :param archived: Filter worklists by whether they are archived or not.
        :param user_id: Filter worklists by the users with permissions.
        :param story_id: Filter worklists by whether they contain a story.
        :param task_id: Filter worklists by whether they contain a task.
        :param hide_lanes: If true, don't return worklists which are lanes in
        a board.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        :param item_type: Used when filtering by story_id. If item_type is
        'story' then only return worklists that contain the story, if
        item_type is 'task' then only return worklists that contain tasks from
        the story, otherwise return worklists that contain the story or tasks
        from the story.
        :param board_id: Get all worklists in the board with this id. Other
        filters are not applied.
        :param subscriber_id: Filter worklists by whether a user is subscribed.
        :param offset: Offset at which to begin the results.
        :param limit: Maximum number of results to return.

        """
        current_user = request.current_user_id

        # If a non existent story/task is requested, there is no point trying
        # to find worklists which contain it
        if story_id:
            story = stories_api.story_get(story_id, current_user=current_user)
            if story is None:
                response.headers['X-Total'] = '0'
                return []
        if task_id:
            task = tasks_api.task_get(task_id, current_user=current_user)
            if task is None:
                response.headers['X-Total'] = '0'
                return []

        worklists = worklists_api.get_all(title=title,
                                          creator_id=creator_id,
                                          project_id=project_id,
                                          archived=archived,
                                          board_id=board_id,
                                          user_id=user_id,
                                          story_id=story_id,
                                          task_id=task_id,
                                          subscriber_id=subscriber_id,
                                          sort_field=sort_field,
                                          sort_dir=sort_dir,
                                          offset=offset,
                                          limit=limit,
                                          current_user=current_user,
                                          hide_lanes=hide_lanes,
                                          item_type=item_type)
        count = worklists_api.get_count(title=title,
                                        creator_id=creator_id,
                                        project_id=project_id,
                                        archived=archived,
                                        board_id=board_id,
                                        user_id=user_id,
                                        story_id=story_id,
                                        task_id=task_id,
                                        subscriber_id=subscriber_id,
                                        current_user=current_user,
                                        hide_lanes=hide_lanes,
                                        item_type=item_type)

        visible_worklists = []
        for worklist in worklists:
            worklist_model = wmodels.Worklist.from_db_model(worklist)
            worklist_model.resolve_permissions(worklist)
            visible_items = worklists_api.get_visible_items(
                worklist, request.current_user_id)
            if not worklist.automatic:
                worklist_model.items = [
                    wmodels.WorklistItem.from_db_model(item)
                    for item in visible_items
                ]
            else:
                worklist_model.items = [
                    wmodels.WorklistItem(**item)
                    for item in worklists_api.filter_items(
                        worklist, request.current_user_id)[0]
                ]
            visible_worklists.append(worklist_model)

        # Apply the query response headers
        response.headers['X-Total'] = str(count)
        if limit is not None:
            response.headers['X-Limit'] = str(limit)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

        return visible_worklists

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Worklist, body=wmodels.Worklist)
    def post(self, worklist):
        """Create a new worklist.

        Example::

          curl https://my.example.org/api/v1/worklists \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"title":"create worklist via api"}'

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
        events_api.worklist_created_event(created_worklist.id,
                                          user_id,
                                          created_worklist.title)

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
        edit = worklists_api.create_permission(
            created_worklist.id, edit_permission)
        move = worklists_api.create_permission(
            created_worklist.id, move_permission)

        event_owners = [{id: users_api.user_get(id).full_name}
                        for id in owners]
        event_users = [{id: users_api.user_get(id).full_name}
                       for id in users]

        events_api.worklist_permission_created_event(created_worklist.id,
                                                     user_id,
                                                     edit.id,
                                                     edit.codename,
                                                     event_owners)
        events_api.worklist_permission_created_event(created_worklist.id,
                                                     user_id,
                                                     move.id,
                                                     move.codename,
                                                     event_users)

        if worklist_dict['automatic']:
            for filter in filters:
                created_filter = worklists_api.create_filter(
                    created_worklist.id, filter.as_dict())
                added = serialize_filter(created_filter)
                events_api.worklist_filters_changed_event(created_worklist.id,
                                                          user_id,
                                                          added=added)

        return wmodels.Worklist.from_db_model(created_worklist)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Worklist, int, body=wmodels.Worklist)
    def put(self, id, worklist):
        """Modify this worklist.

        Example::

          TODO

        :param id: The ID of the worklist.
        :param worklist: A worklist within the request body.

        """
        user_id = request.current_user_id
        if not worklists_api.editable(worklists_api.get(id), user_id):
            raise exc.NotFound(_("Worklist %s not found") % id)

        story_cache = {story.id: story for story in stories_api.story_get_all(
                       worklist_id=id, current_user=user_id)}
        task_cache = {task.id: task for task in tasks_api.task_get_all(
                      worklist_id=id, current_user=user_id)}

        # We don't use this endpoint to update the worklist's contents
        if worklist.items != wtypes.Unset:
            del worklist.items

        # We don't use this endpoint to update the worklist's filters either
        if worklist.filters != wtypes.Unset:
            del worklist.filters

        worklist_dict = worklist.as_dict(omit_unset=True)

        original = copy.deepcopy(worklists_api.get(id))
        updated_worklist = worklists_api.update(id, worklist_dict)

        post_timeline_events(original, updated_worklist)
        if worklists_api.visible(updated_worklist, user_id):
            worklist_model = wmodels.Worklist.from_db_model(updated_worklist)
            worklist_model.resolve_items(
                updated_worklist, story_cache, task_cache)
            worklist_model.resolve_permissions(updated_worklist)
            return worklist_model
        else:
            raise exc.NotFound(_("Worklist %s not found"))

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, worklist_id):
        """Archive this worklist.
           Though this uses the DELETE command, the worklist is not deleted.
           Archived worklists remain viewable at the designated URL, but
           are not returned in search results nor appear on your dashboard.

        Example::

          curl https://my.example.org/api/v1/worklists/30 -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param worklist_id: The ID of the worklist to be archived.

        """
        worklist = worklists_api.get(worklist_id)
        original = copy.deepcopy(worklist)
        user_id = request.current_user_id
        if not worklists_api.editable(worklist, user_id):
            raise exc.NotFound(_("Worklist %s not found") % worklist_id)

        updated = worklists_api.update(worklist_id, {"archived": True})

        post_timeline_events(original, updated)

    items = ItemsSubcontroller()
    permissions = PermissionsController()
    filters = FilterSubcontroller()
