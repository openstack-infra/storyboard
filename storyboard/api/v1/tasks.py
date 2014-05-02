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
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.db.api import tasks as tasks_api

CONF = cfg.CONF


class Task(base.APIBase):
    """A Task represents an actionable work item, targeting a specific Project
    and a specific branch. It is part of a Story. There may be multiple tasks
    in a story, pointing to different projects or different branches. Each task
    is generally linked to a code change proposed in Gerrit.
    """

    title = wtypes.text
    """An optional short label for the task, to show in listings."""

    # TODO(ruhe): replace with enum
    status = wtypes.text
    """Status.
    Allowed values: ['todo', 'inprogress', 'invalid', 'review', 'merged'].
    Human readable versions are left to the UI.
    """

    is_active = bool
    """Is this an active task, or has it been deleted?"""

    creator_id = int
    """Id of the User who has created this Task"""

    story_id = int
    """The ID of the corresponding Story."""

    project_id = int
    """The ID of the corresponding Project."""

    assignee_id = int
    """The ID of the invidiual to whom this task is assigned."""


class TasksController(rest.RestController):
    """Manages tasks."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Task, int)
    def get_one(self, task_id):
        """Retrieve details about one task.

        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(task_id)

        if task:
            return Task.from_db_model(task)
        else:
            raise ClientSideError("Task %s not found" % id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Task], int, int, int, int)
    def get_all(self, story_id=None, assignee_id=None, marker=None,
                limit=None):
        """Retrieve definitions of all of the tasks.

        :param story_id: filter tasks by story ID.
        :param assignee_id: filter tasks by who they are assigned to.
        :param marker: The resource id where the page should begin.
        :param limit: The number of tasks to retrieve.
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_task = tasks_api.task_get(marker)

        if marker_task is None or marker_task.story_id != story_id:
            marker_task = None

        tasks = tasks_api.task_get_all(marker=marker_task,
                                       limit=limit,
                                       assignee_id=assignee_id,
                                       story_id=story_id)
        task_count = tasks_api.task_get_count(assignee_id=assignee_id,
                                              story_id=story_id)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(task_count)
        if marker_task:
            response.headers['X-Marker'] = str(marker_task.id)

        return [Task.from_db_model(s) for s in tasks]

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Task, body=Task)
    def post(self, task):
        """Create a new task.

        :param task: a task within the request body.
        """

        creator_id = request.current_user_id
        task.creator_id = creator_id

        created_task = tasks_api.task_create(task.as_dict())
        return Task.from_db_model(created_task)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Task, int, body=Task)
    def put(self, task_id, task):
        """Modify this task.

        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """
        updated_task = tasks_api.task_update(task_id,
                                             task.as_dict(omit_unset=True))

        if updated_task:
            return Task.from_db_model(updated_task)
        else:
            raise ClientSideError("Task %s not found" % id,
                                  status_code=404)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Task, int)
    def delete(self, task_id):
        """Delete this task.

        :param task_id: An ID of the task.
        """
        tasks_api.task_delete(task_id)

        response.status_code = 204
