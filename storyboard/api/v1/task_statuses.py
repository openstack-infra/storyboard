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
from pecan.secure import secure
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.wmodels import TaskStatus
from storyboard.db.api import tasks as tasks_api


class TaskStatusesController(rest.RestController):
    """Manages tasks statuses."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose([TaskStatus])
    def get(self):
        """Retrieve the possible task statuses
        """
        statuses = tasks_api.task_get_statuses()
        task_statuses = []
        for key, val in statuses.items():
            ts = TaskStatus(key=key, name=val)
            task_statuses.append(ts)
        return task_statuses
