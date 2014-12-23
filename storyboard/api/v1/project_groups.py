# Copyright (c) 2013 Mirantis Inc.
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

from oslo.config import cfg
from pecan import abort
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

import storyboard.api.auth.authorization_checks as checks
from storyboard.api.v1 import wmodels
import storyboard.common.exception as exc
from storyboard.db.api import project_groups
from storyboard.db.api import projects
from storyboard.openstack.common.gettextutils import _  # noqa


CONF = cfg.CONF


class ProjectsSubcontroller(rest.RestController):
    """This controller should be used to list, add or remove projects from a
    Project Group.
    """

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Project], int)
    def get(self, project_group_id):
        """Get projects inside a project group.

        :param project_group_id: An ID of the project group
        """

        project_group = project_groups.project_group_get(project_group_id)

        if not project_group:
            raise ClientSideError(_("The requested project "
                                    "group does not exist"))

        return [wmodels.Project.from_db_model(project)
                for project in project_group.projects]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Project, int, int)
    def put(self, project_group_id, project_id):
        """Add a project to a project_group
        """

        project_groups.project_group_add_project(project_group_id, project_id)

        return wmodels.Project.from_db_model(projects.project_get(project_id))

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(None, int, int)
    def delete(self, project_group_id, project_id):
        """Delete a project from a project_group
        """
        project_groups.project_group_delete_project(project_group_id,
                                                    project_id)

        response.status_code = 204


class ProjectGroupsController(rest.RestController):
    """REST controller for Project Groups.

    NOTE: PUT requests should be used to update only top-level fields.
    The nested fields (projects) should be updated using requests to a
    /projects subcontroller
    """

    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.ProjectGroup, int)
    def get_one(self, project_group_id):
        """Retrieve information about the given project group.

        :param project_group_id: project group id.
        """

        group = project_groups.project_group_get(project_group_id)
        if not group:
            raise ClientSideError(_("Project Group %s not found") %
                                  project_group_id,
                                  status_code=404)

        return wmodels.ProjectGroup.from_db_model(group)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.ProjectGroup], int, int, unicode, unicode,
                         unicode, unicode)
    def get(self, marker=None, limit=None, name=None, title=None,
            sort_field='id', sort_dir='asc'):
        """Retrieve a list of projects groups."""

        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_group = project_groups.project_group_get(marker)

        groups = project_groups.project_group_get_all(marker=marker_group,
                                                      limit=limit,
                                                      name=name,
                                                      title=title,
                                                      sort_field=sort_field,
                                                      sort_dir=sort_dir)

        group_count = project_groups.project_group_get_count(name=name,
                                                             title=title)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(group_count)
        if marker_group:
            response.headers['X-Marker'] = str(marker_group.id)

        return [wmodels.ProjectGroup.from_db_model(group) for group in groups]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.ProjectGroup, body=wmodels.ProjectGroup)
    def post(self, project_group):
        """Create a new project group.

        :param project_group: a project group within the request body.
        """

        created_group = project_groups.project_group_create(
            project_group.as_dict())

        if not created_group:
            raise ClientSideError(_("Could not create ProjectGroup"))

        return wmodels.ProjectGroup.from_db_model(created_group)

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.ProjectGroup, int, body=wmodels.ProjectGroup)
    def put(self, project_group_id, project_group):
        """Modify this project group.

        :param project_group_id: An ID of the project group.
        :param project_group: a project group within the request body.
        """

        updated_group = project_groups.project_group_update(
            project_group_id,
            project_group.as_dict(omit_unset=True))

        if not updated_group:
            raise ClientSideError(_("Could not update group %s") %
                                  project_group_id)

        return wmodels.ProjectGroup.from_db_model(updated_group)

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(None, int)
    def delete(self, project_group_id):
        """Delete this project group.

        :param project_group_id: An ID of the project group.
        """
        try:
            project_groups.project_group_delete(project_group_id)
        except exc.NotFound as not_found_exc:
            abort(404, not_found_exc.message)
        except exc.NotEmpty as not_empty_exc:
            abort(400, not_empty_exc.message)

        response.status_code = 204

    projects = ProjectsSubcontroller()
