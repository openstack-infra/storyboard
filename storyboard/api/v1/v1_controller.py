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

from storyboard.api.v1.auth import AuthController
from storyboard.api.v1.project_groups import ProjectGroupsController
from storyboard.api.v1.projects import ProjectsController
from storyboard.api.v1.stories import StoriesController
from storyboard.api.v1.tasks import TasksController
from storyboard.api.v1.teams import TeamsController
from storyboard.api.v1.users import UsersController


class V1Controller(object):

    project_groups = ProjectGroupsController()
    projects = ProjectsController()
    users = UsersController()
    teams = TeamsController()
    stories = StoriesController()
    tasks = TasksController()

    openid = AuthController()
