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


class ProjectsTest(base.DbTestCase):

    def setUp(self):
        super(ProjectsTest, self).setUp()

        self.project_01 = {
            'name': u'StoryBoard',
            'description': u'Awesome Task Tracker'
        }

    def test_save_project(self):
        ref = self.project_01
        saved = dbapi.project_create(ref)

        self.assertIsNotNone(saved.id)
        self.assertEqual(ref['name'], saved.name)
        self.assertEqual(ref['description'], saved.description)

    def test_update_project(self):
        saved = dbapi.project_create(self.project_01)
        delta = {
            'name': u'New Name',
            'description': u'New Description'
        }
        updated = dbapi.project_update(saved.id, delta)

        self.assertEqual(saved.id, updated.id)
        self.assertEqual(delta['name'], updated.name)
        self.assertEqual(delta['description'], updated.description)


class StoriesTest(base.DbTestCase):

    def setUp(self):
        super(StoriesTest, self).setUp()

        self.story_01 = {
            'title': u'Worst Story Ever',
            'description': u'Story description'
        }

    def test_create_story(self):
        ref = self.story_01
        saved = dbapi.story_create(self.story_01)

        self.assertIsNotNone(saved.id)
        self.assertEqual(ref['title'], saved.title)
        self.assertEqual(ref['description'], saved.description)

    def test_update_story(self):
        saved = dbapi.story_create(self.story_01)
        delta = {
            'title': u'New Title',
            'description': u'New Description'
        }

        updated = dbapi.story_update(saved.id, delta)

        self.assertEqual(saved.id, updated.id)
        self.assertEqual(delta['title'], updated.title)
        self.assertEqual(delta['description'], updated.description)
