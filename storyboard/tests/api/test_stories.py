# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from storyboard.tests import base


class TestStories(base.FunctionalTest):

    def setUp(self):
        super(TestStories, self).setUp()
        self.resource = '/stories'

        self.story_01 = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker'
        }
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_stories_endpoint(self):
        response = self.get_json(self.resource, project_id=1)
        self.assertEqual([], response)

    def test_create(self):
        response = self.post_json(self.resource, self.story_01)
        story = json.loads(response.body)

        url = "%s/%d" % (self.resource, story['id'])
        story = self.get_json(url)

        self.assertIn('id', story)
        self.assertIn('created_at', story)
        self.assertEqual(story['title'], self.story_01['title'])
        self.assertEqual(story['description'], self.story_01['description'])

    def test_update(self):
        response = self.post_json(self.resource, self.story_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'title': 'new title',
            'description': 'new description'
        }

        url = "/stories/%d" % original['id']
        response = self.put_json(url, delta)
        updated = json.loads(response.body)

        self.assertEqual(updated['id'], original['id'])

        self.assertNotEqual(updated['title'], original['title'])
        self.assertNotEqual(updated['description'],
                            original['description'])
