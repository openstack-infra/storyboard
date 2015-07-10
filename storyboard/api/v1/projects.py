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

from oslo_config import cfg
from pecan.decorators import expose
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import projects as projects_api
from storyboard.openstack.common.gettextutils import _  # noqa


CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class ProjectsController(rest.RestController):
    """REST controller for Projects.

    At this moment it provides read-only operations.
    """

    _custom_actions = {"search": ["GET"]}

    validation_post_schema = validations.PROJECTS_POST_SCHEMA
    validation_put_schema = validations.PROJECTS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Project, int)
    def get_one_by_id(self, project_id):
        """Retrieve information about the given project.

        :param project_id: Project ID.
        """

        project = projects_api.project_get(project_id)

        if project:
            return wmodels.Project.from_db_model(project)
        else:
            raise exc.NotFound(_("Project %s not found") % project_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Project, wtypes.text)
    def get_one_by_name(self, project_name):
        """Retrieve information about the given project.

        :param name: Project name.
        """

        project = projects_api.project_get_by_name(project_name)

        if project:
            return wmodels.Project.from_db_model(project)
        else:
            raise exc.NotFound(_("Project %s not found") % project_name)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Project], int, int, int, wtypes.text,
                         wtypes.text, int, wtypes.text, wtypes.text)
    def get(self, marker=None, offset=None, limit=None, name=None,
            description=None, project_group_id=None, sort_field='id',
            sort_dir='asc'):
        """Retrieve a list of projects.

        :param marker: The resource id where the page should begin.
        :param offset: The offset to start the page at.
        :param limit: The number of projects to retrieve.
        :param name: A string to filter the name by.
        :param description: A string to filter the description by.
        :param project_group_id: The ID of a project group to which the
                                 projects must belong.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_project = None
        if marker is not None:
            marker_project = projects_api.project_get(marker)

        projects = \
            projects_api.project_get_all(marker=marker_project,
                                         offset=offset,
                                         limit=limit,
                                         name=name,
                                         description=description,
                                         project_group_id=project_group_id,
                                         sort_field=sort_field,
                                         sort_dir=sort_dir)
        project_count = \
            projects_api.project_get_count(name=name,
                                           description=description,
                                           project_group_id=project_group_id)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(project_count)
        if marker_project:
            response.headers['X-Marker'] = str(marker_project.id)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

        return [wmodels.Project.from_db_model(p) for p in projects]

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Project, body=wmodels.Project)
    def post(self, project):
        """Create a new project.

        :param project: A project within the request body.
        """

        result = projects_api.project_create(project.as_dict())
        return wmodels.Project.from_db_model(result)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Project, int, body=wmodels.Project)
    def put(self, project_id, project):
        """Modify this project.

        :param project_id: An ID of the project.
        :param project: A project within the request body.
        """
        result = projects_api.project_update(project_id,
                                             project.as_dict(omit_unset=True))

        if result:
            return wmodels.Project.from_db_model(result)
        else:
            raise exc.NotFound(_("Project %s not found") % project_id)

    def _is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Project], wtypes.text, wtypes.text, int,
                         int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for projects.

        :param q: The query string.
        :return: List of Projects matching the query.
        """

        projects = SEARCH_ENGINE.projects_query(q=q, marker=marker,
                                                limit=limit)

        return [wmodels.Project.from_db_model(project) for project in projects]

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) > 0:
            # It's a request by a name or id
            something = args[0]

            if something == "search":
                # Request to a search endpoint
                return super(ProjectsController, self)._route(args, request)

            if self._is_int(something):
                # Get by id
                return self.get_one_by_id, args
            else:
                # Get by name
                return self.get_one_by_name, ["/".join(args)]

        # Use default routing for all other requests
        return super(ProjectsController, self)._route(args, request)
