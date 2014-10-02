# Copyright (c) 2014 Mirantis Inc.
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

from storyboard.db.models import Story
from storyboard.db.models import User
from storyboard.tests import base


class TestComments(base.FunctionalTest):

    def setUp(self):
        super(TestComments, self).setUp()
        self.comments_resource = '/stories/%s/comments'

        # pre load data:
        self.load_data([
            Story(id=1,
                  title='StoryBoard',
                  description='Awesome Task Tracker',
                  priority='High'),
            User(id=1,
                 username='active',
                 email='active@example.com',
                 full_name='Active User',
                 is_superuser=True)
        ])
        self.story_id = 1

        self.comment_01 = {
            'content': 'Just a comment passing by'
        }
        self.comment_02 = {
            'content': 'And another one'
        }

        active_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            active_token.access_token)

    def test_comments_endpoint(self):
        response = self.get_json(self.comments_resource % self.story_id)
        self.assertEqual(0, len(response))

    def test_create(self):
        self.post_json(self.comments_resource % self.story_id, self.comment_01)
        self.post_json(self.comments_resource % self.story_id, self.comment_02)

        all_comments = self.get_json(self.comments_resource % self.story_id)
        self.assertEqual(2, len(all_comments))

        non_existing_comments = self.get_json(self.comments_resource % "123")
        self.assertEqual([], non_existing_comments)

    def test_update(self):
        original = self.post_json(self.comments_resource % self.story_id,
                                  self.comment_01)

        original_event = json.loads(original.body)

        delta = {
            'id': original_event['comment_id'],
            'content': 'Updated content',
            'is_active': True
        }
        original_id = original_event['comment_id']
        update_url = self.comments_resource % self.story_id + \
            "/%d" % original_id

        updated = self.put_json(update_url, delta)

        original_content = self.comment_01['content']
        updated_content = json.loads(updated.body)['content']

        self.assertNotEqual(original_content, updated_content)
