# Copyright (c) 2015 Mirantis Inc.
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

import six

from storyboard.common import exception as exc
from storyboard.db.api import projects
from storyboard.db.api import tasks
from storyboard.tests import base


class TestDBDuplicateEntry(base.DbTestCase):
    def setUp(self):
        super(TestDBDuplicateEntry, self).setUp()

    # create two projects with equal names
    def test_users(self):
        project = {
            'id': 10,
            'name': 'project',
            'description': 'Project 4 Description - foo'
        }

        projects.project_create(project)
        self.assertRaises(exc.DBDuplicateEntry,
                          lambda: projects.project_create(project))


class TestDBReferenceError(base.DbTestCase):
    def setUp(self):
        super(TestDBReferenceError, self).setUp()

    # create task with id of not existing story
    def test_teams(self):
        task = {
            'id': 10,
            'story_id': 100
        }

        self.assertRaises(exc.DBReferenceError,
                          lambda: tasks.task_create(task))


class TestDbInvalidSortKey(base.DbTestCase):
    def setUp(self):
        super(TestDbInvalidSortKey, self).setUp()

    # create project and sort his field with incorrect key
    def test_projects(self):
        project = {
            'id': 10,
            'name': 'testProject',
            'description': 'testProjectDescription'
        }

        saved_project = projects.project_create(project)
        self.assertIsNotNone(saved_project)

        for k, v in six.iteritems(project):
            self.assertEqual(saved_project[k], v)

        self.assertRaises(exc.DBInvalidSortKey,
                          lambda: projects.project_get_all(
                              marker=10,
                              sort_field='invalid_sort_field'))
