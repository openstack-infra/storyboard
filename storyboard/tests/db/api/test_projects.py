# Copyright (c) 2015 Mirantis Inc.
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

from storyboard.db.api import projects
from storyboard.tests.db import base


class ProjectsTest(base.BaseDbTestCase):

    def setUp(self):
        super(ProjectsTest, self).setUp()

        self.project_01 = {
            'name': u'StoryBoard',
            'description': u'Awesome Task Tracker'
        }

    def test_save_project(self):
        self._test_create(self.project_01, projects.project_create)

    def test_update_project(self):
        delta = {
            'name': u'New Name',
            'description': u'New Description'
        }
        self._test_update(self.project_01, delta,
                          projects.project_create, projects.project_update)
