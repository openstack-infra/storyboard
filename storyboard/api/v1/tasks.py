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

from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.v1 import base
from storyboard.db import api as dbapi


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
    Allowed values: ['Todo', 'In review', 'Landed'].
    """

    story_id = int
    """The ID of the corresponding Story."""

    project_id = int
    """The ID of the corresponding Project."""


class TasksController(rest.RestController):
    """Manages tasks."""

    @wsme_pecan.wsexpose(Task, int)
    def get_one(self, task_id):
        """Retrieve details about one task.

        :param task_id: An ID of the task.
        """
        task = dbapi.task_get(task_id)
        return Task.from_db_model(task)

    @wsme_pecan.wsexpose([Task], int)
    def get_all(self, story_id=None):
        """Retrieve definitions of all of the tasks.

        :param story_id: filter tasks by story ID.
        """
        tasks = dbapi.task_get_all(story_id=story_id)
        return [Task.from_db_model(s) for s in tasks]

    @wsme_pecan.wsexpose(Task, body=Task)
    def post(self, task):
        """Create a new task.

        :param task: a task within the request body.
        """
        created_task = dbapi.task_create(task.as_dict())
        return Task.from_db_model(created_task)

    @wsme_pecan.wsexpose(Task, int, body=Task)
    def put(self, task_id, task):
        """Modify this task.

        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """
        updated_task = dbapi.task_update(task_id,
                                         task.as_dict(omit_unset=True))
        return Task.from_db_model(updated_task)
