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

from storyboard.db.api import branches
from storyboard.db.api import milestones
from storyboard.db.api import projects
from storyboard.tests.db import base


class MilestonesTest(base.BaseDbTestCase):
    def setUp(self):
        super(MilestonesTest, self).setUp()

        self.milestone_01 = {
            'name': u'test_milestone',
            'branch_id': 1
        }

        self.branch_01 = {
            'name': u'test_branch',
            'project_id': 1
        }

        self.project_01 = {
            'name': u'TestProject',
            'description': u'TestDescription'
        }

        projects.project_create(self.project_01)
        branches.branch_create(self.branch_01)

    def test_create_branch(self):
        self._test_create(self.milestone_01, milestones.milestone_create)

    def test_update_branch(self):
        delta = {
            'expired': True
        }

        self._test_update(self.milestone_01, delta,
                          milestones.milestone_create,
                          milestones.milestone_update)
