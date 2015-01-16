# Copyright (c) 2013 Mirantis Inc.
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

from oslo.config import cfg
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api
from storyboard.openstack.common.gettextutils import _  # noqa

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class TasksController(rest.RestController):
    """Manages tasks."""

    _custom_actions = {"search": ["GET"]}

    validation_post_schema = validations.TASKS_POST_SCHEMA
    validation_put_schema = validations.TASKS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Task, int)
    def get_one(self, task_id):
        """Retrieve details about one task.

        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(task_id)

        if task:
            return wmodels.Task.from_db_model(task)
        else:
            raise ClientSideError(_("Task %s not found") % task_id,
                                  status_code=404)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], unicode, int, int, int, int,
                         [unicode], [unicode], int, int, unicode, unicode)
    def get_all(self, title=None, story_id=None, assignee_id=None,
                project_id=None, project_group_id=None, status=None,
                priority=None, marker=None, limit=None, sort_field='id',
                sort_dir='asc'):
        """Retrieve definitions of all of the tasks.

        :param title: search by task title.
        :param story_id: filter tasks by story ID.
        :param assignee_id: filter tasks by who they are assigned to.
        :param project_id: filter the tasks based on project.
        :param project_group_id: filter tasks based on project group.
        :param status: filter tasks by status.
        :param priority: filter tasks by priority.
        :param marker: The resource id where the page should begin.
        :param limit: The number of tasks to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_task = tasks_api.task_get(marker)

        tasks = tasks_api \
            .task_get_all(title=title,
                          story_id=story_id,
                          assignee_id=assignee_id,
                          project_id=project_id,
                          project_group_id=project_group_id,
                          status=status,
                          priority=priority,
                          sort_field=sort_field,
                          sort_dir=sort_dir,
                          marker=marker_task,
                          limit=limit)
        task_count = tasks_api \
            .task_get_count(title=title,
                            story_id=story_id,
                            assignee_id=assignee_id,
                            project_id=project_id,
                            project_group_id=project_group_id,
                            status=status,
                            priority=priority)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(task_count)
        if marker_task:
            response.headers['X-Marker'] = str(marker_task.id)

        return [wmodels.Task.from_db_model(s) for s in tasks]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, body=wmodels.Task)
    def post(self, task):
        """Create a new task.

        :param task: a task within the request body.
        """

        creator_id = request.current_user_id
        task.creator_id = creator_id

        created_task = tasks_api.task_create(task.as_dict())

        events_api.task_created_event(story_id=task.story_id,
                                      task_id=created_task.id,
                                      task_title=created_task.title,
                                      author_id=creator_id)

        return wmodels.Task.from_db_model(created_task)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, body=wmodels.Task)
    def put(self, task_id, task):
        """Modify this task.

        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """
        original_task = tasks_api.task_get(task_id)

        updated_task = tasks_api.task_update(task_id,
                                             task.as_dict(omit_unset=True))

        if updated_task:
            self._post_timeline_events(original_task, updated_task)
            return wmodels.Task.from_db_model(updated_task)
        else:
            raise ClientSideError(_("Task %s not found") % task_id,
                                  status_code=404)

    def _post_timeline_events(self, original_task, updated_task):
        # If both the assignee_id and the status were changed there will be
        # two separate comments in the activity log.

        author_id = request.current_user_id
        specific_change = False

        if original_task.status != updated_task.status:
            events_api.task_status_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_status=original_task.status,
                new_status=updated_task.status)
            specific_change = True

        if original_task.priority != updated_task.priority:
            events_api.task_priority_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_priority=original_task.priority,
                new_priority=updated_task.priority)
            specific_change = True

        if original_task.assignee_id != updated_task.assignee_id:
            events_api.task_assignee_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_assignee_id=original_task.assignee_id,
                new_assignee_id=updated_task.assignee_id)
            specific_change = True

        if not specific_change:
            events_api.task_details_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int)
    def delete(self, task_id):
        """Delete this task.

        :param task_id: An ID of the task.
        """
        original_task = tasks_api.task_get(task_id)

        events_api.task_deleted_event(
            story_id=original_task.story_id,
            task_id=original_task.id,
            task_title=original_task.title,
            author_id=request.current_user_id)

        tasks_api.task_delete(task_id)

        response.status_code = 204

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], unicode, unicode, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for tasks.

        :param q: The query string.
        :return: List of Tasks matching the query.
        """

        tasks = SEARCH_ENGINE.tasks_query(q=q,
                                          marker=marker,
                                          limit=limit)

        return [wmodels.Task.from_db_model(task) for task in tasks]
