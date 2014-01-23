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

    @wsme_pecan.wsexpose(wsme_models.ProjectGroup, int)
    def get_one(self, id):
        group = wsme_models.ProjectGroup.get(id=id)
        if not group:
            raise ClientSideError("Project Group %s not found" % id,
                                  status_code=404)
        return group

    @wsme_pecan.wsexpose([wsme_models.ProjectGroup])
    def get(self):
        groups = wsme_models.ProjectGroup.get_all()
        return groups

    @wsme_pecan.wsexpose(wsme_models.ProjectGroup,
                         body=wsme_models.ProjectGroup)
    def post(self, group):
        created_group = wsme_models.ProjectGroup.create(wsme_entry=group)
        if not created_group:
            raise ClientSideError("Could not create ProjectGroup")
        return created_group

    @wsme_pecan.wsexpose(wsme_models.ProjectGroup, int,
                         body=wsme_models.ProjectGroup)
    def put(self, id, group):
        updated_group = wsme_models.ProjectGroup.update("id", id, group)
        if not updated_group:
            raise ClientSideError("Could not update group %s" % id)
        return updated_group
