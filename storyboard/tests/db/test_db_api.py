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

from storyboard.db import api as dbapi
from storyboard.tests import base


class BaseDbTestCase(base.DbTestCase):
    def setUp(self):
        super(BaseDbTestCase, self).setUp()

    def _assert_saved_fields(self, expected, actual):
        for k in expected.keys():
            self.assertEqual(expected[k], actual[k])

    def _test_create(self, ref, save_method):
        saved = save_method(ref)

        self.assertIsNotNone(saved.id)
        self._assert_saved_fields(ref, saved)

    def _test_update(self, ref, delta, create, update):
        saved = create(ref)
        updated = update(saved.id, delta)

        self.assertEqual(saved.id, updated.id)
        self._assert_saved_fields(delta, updated)


class ProjectsTest(BaseDbTestCase):

    def setUp(self):
        super(ProjectsTest, self).setUp()

        self.project_01 = {
            'name': u'StoryBoard',
            'description': u'Awesome Task Tracker'
        }

    def test_save_project(self):
        self._test_create(self.project_01, dbapi.project_create)

    def test_update_project(self):
        delta = {
            'name': u'New Name',
            'description': u'New Description'
        }
        self._test_update(self.project_01, delta,
                          dbapi.project_create, dbapi.project_update)


class StoriesTest(BaseDbTestCase):

    def setUp(self):
        super(StoriesTest, self).setUp()

        self.story_01 = {
            'title': u'Worst Story Ever',
            'description': u'Story description'
        }

    def test_create_story(self):
        self._test_create(self.story_01, dbapi.story_create)

    def test_update_story(self):
        delta = {
            'title': u'New Title',
            'description': u'New Description'
        }
        self._test_update(self.story_01, delta,
                          dbapi.story_create, dbapi.story_update)


class TasksTest(BaseDbTestCase):

    def setUp(self):
        super(TasksTest, self).setUp()

        self.task_01 = {
            'title': u'Invent time machine',
            'status': 'Todo',
            'story_id': 1
        }

    def test_create_task(self):
        self._test_create(self.task_01, dbapi.task_create)

    def test_update_task(self):
        delta = {
            'status': 'In review',
            'assignee_id': 1
        }

        self._test_update(self.task_01, delta,
                          dbapi.task_create, dbapi.task_update)
