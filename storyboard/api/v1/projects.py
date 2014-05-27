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
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.common import custom_types
from storyboard.db.api import projects as projects_api

CONF = cfg.CONF


class Project(base.APIBase):
    """The Storyboard Registry describes the open source world as ProjectGroups
    and Projects. Each ProjectGroup may be responsible for several Projects.
    For example, the OpenStack Infrastructure ProjectGroup has Zuul, Nodepool,
    Storyboard as Projects, among others.
    """

    name = custom_types.Name()
    """At least three letters or digits. Also brackets, underscore, and
    whitespaces are allowed.
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

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Project, unicode)
    def get_one(self, project_id):
        """Retrieve information about the given project.

        :param project_id: project ID.
        """

        project = projects_api.project_get(project_id)

        if project:
            return Project.from_db_model(project)
        else:
            raise ClientSideError("Project %s not found" % id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Project], int, int, unicode, unicode)
    def get(self, marker=None, limit=None, name=None, description=None):
        """Retrieve a list of projects.

        :param marker: The resource id where the page should begin.
        :param limit: The number of projects to retrieve.
        :param name: A string to filter the name by.
        :param description: A string to filter the description by.
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
                                                description=description)
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
