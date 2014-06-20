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
from pecan.decorators import expose
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.api.v1.search import search_engine
from storyboard.common.custom_types import NameType
from storyboard.db.api import projects as projects_api

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class Project(base.APIBase):
    """The Storyboard Registry describes the open source world as ProjectGroups
    and Projects. Each ProjectGroup may be responsible for several Projects.
    For example, the OpenStack Infrastructure ProjectGroup has Zuul, Nodepool,
    Storyboard as Projects, among others.
    """

    name = NameType()
    """The Project unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols. Minus and dot symbols are allowed as
    separators.
    """

    description = wtypes.text
    """Details about the project's work, highlights, goals, and how to
    contribute. Use plain text, paragraphs are preserved and URLs are
    linked in pages.
    """

    is_active = bool
    """Is this an active project, or has it been deleted?"""

    @classmethod
    def sample(cls):
        return cls(
            name="StoryBoard",
            description="This is an awesome project.",
            is_active=True)


class ProjectsController(rest.RestController):
    """REST controller for Projects.

    At this moment it provides read-only operations.
    """

    _custom_actions = {"search": ["GET"]}

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Project, int)
    def get_one_by_id(self, project_id):
        """Retrieve information about the given project.

        :param project_id: project ID.
        """

        project = projects_api.project_get(project_id)

        if project:
            return Project.from_db_model(project)
        else:
            raise ClientSideError("Project %s not found" % project_id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Project, unicode)
    def get_one_by_name(self, project_name):
        """Retrieve information about the given project.

        :param name: project name.
        """

        project = projects_api.project_get_by_name(project_name)

        if project:
            return Project.from_db_model(project)
        else:
            raise ClientSideError("Project %s not found" % project_name,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Project], int, int, unicode, unicode, unicode,
                         unicode)
    def get(self, marker=None, limit=None, name=None, description=None,
            sort_field='id', sort_dir='asc'):
        """Retrieve a list of projects.

        :param marker: The resource id where the page should begin.
        :param limit: The number of projects to retrieve.
        :param name: A string to filter the name by.
        :param description: A string to filter the description by.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """
        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_project = projects_api.project_get(marker)

        projects = projects_api.project_get_all(marker=marker_project,
                                                limit=limit,
                                                name=name,
                                                description=description,
                                                sort_field=sort_field,
                                                sort_dir=sort_dir)
        project_count = projects_api.project_get_count(name=name,
                                                       description=description)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(project_count)
        if marker_project:
            response.headers['X-Marker'] = str(marker_project.id)

        return [Project.from_db_model(p) for p in projects]

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(Project, body=Project)
    def post(self, project):
        """Create a new project.

        :param project: a project within the request body.
        """
        result = projects_api.project_create(project.as_dict())
        return Project.from_db_model(result)

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(Project, int, body=Project)
    def put(self, project_id, project):
        """Modify this project.

        :param project_id: An ID of the project.
        :param project: a project within the request body.
        """
        result = projects_api.project_update(project_id,
                                             project.as_dict(omit_unset=True))

        if result:
            return Project.from_db_model(result)
        else:
            raise ClientSideError("Project %s not found" % id,
                                  status_code=404)

    def _is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Project], unicode, unicode, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for projects.

        :param q: The query string.
        :return: List of Projects matching the query.
        """

        projects = SEARCH_ENGINE.projects_query(q=q, marker=marker,
                                                limit=limit)

        return [Project.from_db_model(project) for project in projects]

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
