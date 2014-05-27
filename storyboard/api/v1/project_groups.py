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
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

import storyboard.api.auth.authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.api.v1.projects import Project
from storyboard.db.api import project_groups


CONF = cfg.CONF


class ProjectGroup(base.APIBase):
    """Represents a group of projects."""

    name = wtypes.text
    """A unique name, used in URLs, identifying the project group. All
    lowercase, no special characters. Examples: infra, compute.
    """

    title = wtypes.text
    """The full name of the project group, which can contain spaces, special
    characters, etc.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="Infra",
            title="Awesome projects")


class ProjectsSubcontroller(rest.RestController):
    """This controller should be used to list, add or remove projects from a
    Project Group.
    """

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Project], int)
    def get(self, project_group_id):
        """Get projects inside a project group.

        :param project_group_id: An ID of the project group
        """

        project_group = project_groups.project_group_get(project_group_id)

        if not project_group:
            raise ClientSideError("The requested project group does not exist")

        return [Project.from_db_model(project)
                for project in project_group.projects]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose([Project], int, int)
    def put(self, project_group_id, project_id):
        """Add a project to a project_group
        """

        project_groups.project_group_add_project(project_group_id, project_id)

        project_group = project_groups.project_group_get(project_group_id)

        return [Project.from_db_model(project)
                for project in project_group.projects]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose([Project], int, int)
    def delete(self, project_group_id, project_id):
        """Delete a project from a project_group
        """
        project_groups.project_group_delete_project(project_group_id,
                                                    project_id)

        project_group = project_groups.project_group_get(project_group_id)

        return [Project.from_db_model(project)
                for project in project_group.projects]


class ProjectGroupsController(rest.RestController):
    """REST controller for Project Groups.

    NOTE: PUT requests should be used to update only top-level fields.
    The nested fields (projects) should be updated using requests to a
    /projects subcontroller
    """

    @secure(checks.guest)
    @wsme_pecan.wsexpose(ProjectGroup, int)
    def get_one(self, project_group_id):
        """Retrieve information about the given project group.

        :param project_group_id: project group id.
        """

        group = project_groups.project_group_get(project_group_id)
        if not group:
            raise ClientSideError("Project Group %s not found" %
                                  project_group_id,
                                  status_code=404)

        return ProjectGroup.from_db_model(group)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([ProjectGroup], int, int, unicode, unicode)
    def get(self, marker=None, limit=None, sort_field='id', sort_dir='asc'):
        """Retrieve a list of projects groups."""

        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        groups = project_groups.project_group_get_all(marker=marker,
                                                      limit=limit,
                                                      sort_field=sort_field,
                                                      sort_dir=sort_dir)

        return [ProjectGroup.from_db_model(group) for group in groups]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(ProjectGroup, body=ProjectGroup)
    def post(self, project_group):
        """Create a new project group.

        :param project_group: a project group within the request body.
        """

        created_group = project_groups.project_group_create(
            project_group.as_dict())

        if not created_group:
            raise ClientSideError("Could not create ProjectGroup")

        return ProjectGroup.from_db_model(created_group)

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(ProjectGroup, int, body=ProjectGroup)
    def put(self, id, project_group):
        """Modify this project group.

        :param id: An ID of the project group.
        :param project_group: a project group within the request body.
        """

        updated_group = project_groups.project_group_update(
            id,
            project_group.as_dict())

        if not updated_group:
            raise ClientSideError("Could not update group %s" % id)

        return ProjectGroup.from_db_model(updated_group)

    projects = ProjectsSubcontroller()
