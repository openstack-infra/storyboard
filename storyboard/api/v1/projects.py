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


class Project(base.APIBase):
    """The Storyboard Registry describes the open source world as ProjectGroups
    and Projects. Each ProjectGroup may be responsible for several Projects.
    For example, the OpenStack Infrastructure ProjectGroup has Zuul, Nodepool,
    Storyboard as Projects, among others.
    """

    name = wtypes.text
    """At least one lowercase letter or number, followed by letters, numbers,
    dots, hyphens or pluses. Keep this name short; it is used in URLs.
    """

    description = wtypes.text
    """Details about the project's work, highlights, goals, and how to
    contribute. Use plain text, paragraphs are preserved and URLs are
    linked in pages.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="StoryBoard",
            description="This is an awesome project.")


class ProjectsController(rest.RestController):
    """REST controller for Projects.

    At this moment it provides read-only operations.
    """

    @wsme_pecan.wsexpose(Project, unicode)
    def get_one(self, project_id):
        """Retrieve information about the given project.

        :param project_id: project ID.
        """

        project = dbapi.project_get(project_id)
        return Project.from_db_model(project)

    @wsme_pecan.wsexpose([Project])
    def get_all(self):
        """Retrieve a list of projects.
        """
        projects = dbapi.project_get_all()
        return [Project.from_db_model(p) for p in projects]

    @wsme_pecan.wsexpose(Project, body=Project)
    def post(self, project):
        """Create a new project.

        :param project: a project within the request body.
        """
        result = dbapi.project_create(project.as_dict())
        return Project.from_db_model(result)

    @wsme_pecan.wsexpose(Project, int, body=Project)
    def put(self, project_id, project):
        """Modify this project.

        :param project_id: An ID of the project.
        :param project: a project within the request body.
        """
        result = dbapi.project_update(project_id,
                                      project.as_dict(omit_unset=True))
        return Project.from_db_model(result)
