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
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

import storyboard.api.v1.wsme_models as wsme_models


class TasksController(rest.RestController):
    """Manages tasks."""

    @wsme_pecan.wsexpose(wsme_models.Task, unicode)
    def get_one(self, id):
        """Retrieve details about one task.

        :param id: An ID of the task.
        """
        task = wsme_models.Task.get(id=id)
        if not task:
            raise ClientSideError("Task %s not found" % id,
                                  status_code=404)
        return task

    @wsme_pecan.wsexpose([wsme_models.Task])
    def get(self):
        """Retrieve definitions of all of the tasks."""
        tasks = wsme_models.Task.get_all()
        return tasks

    @wsme_pecan.wsexpose(wsme_models.Task, unicode, wsme_models.Task)
    def put(self, task_id, task):
        """Modify this task.

        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """
        updated_task = wsme_models.Task.update("id", task_id, task)
        if not updated_task:
            raise ClientSideError("Could not update story %s" % task_id)
        return updated_task
