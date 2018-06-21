# Copyright (c) 2014 Mirantis Inc.
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

import sys

import mock
import testscenarios

from storyboard.db.api import base as db_api_base
from storyboard.db.migration import cli
from storyboard.db import models
from storyboard.tests.db import base


class TestLoadProjects(base.BaseDbTestCase):

    scenarios = [
        ('do_load_projects',
         dict(argv=['prog', 'load_projects',
                    'etc/projects.yaml.sample'],
              func_name='load_projects'))
    ]

    def test_cli(self):
        with mock.patch.object(sys, 'argv', self.argv):
            cli.main()
            session = db_api_base.get_session()
            project_groups = session.query(models.ProjectGroup).all()
            projects = session.query(models.Project).all()

            self.assertIsNotNone(project_groups)
            self.assertIsNotNone(projects)

            # Loaded + mock_data
            project_names = ["Test-Project", "Test-Project-Two",
                             "project1", "project2", "tests/project3"]
            project_ids = []
            for project in projects:
                self.assertIn(project.name, project_names)
                project_ids.append(project.id)
                project_names.remove(project.name)

            # call again and nothing should change
            cli.main()

            session = db_api_base.get_session()
            projects = session.query(models.Project).all()

            self.assertIsNotNone(projects)
            for project in projects:
                self.assertIn(project.id, project_ids)


def load_tests(loader, in_tests, pattern):
    return testscenarios.load_tests_apply_scenarios(loader, in_tests, pattern)
