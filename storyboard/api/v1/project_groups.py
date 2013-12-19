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


class ProjectGroupsController(rest.RestController):

    @wsme_pecan.wsexpose(wsme_models.ProjectGroup, unicode)
    def get_one(self, name):
        group = wsme_models.ProjectGroup.get(name=name)
        if not group:
            raise ClientSideError("Project Group %s not found" % name,
                                  status_code=404)
        return group

    @wsme_pecan.wsexpose([wsme_models.ProjectGroup])
    def get(self):
        groups = wsme_models.ProjectGroup.get_all()
        return groups
