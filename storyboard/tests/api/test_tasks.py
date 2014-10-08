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

from storyboard.db.models import Story
from storyboard.db.models import User
from storyboard.tests import base


class TestTasks(base.FunctionalTest):

    def setUp(self):
        super(TestTasks, self).setUp()
        self.resource = '/tasks'

        self.task_01 = {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 1
        }

        self.load_data([
            User(id=1,
                 username='superuser',
                 email='superuser@example.com',
                 full_name='Super User',
                 is_superuser=True),
            Story(name="Test Story"),
            Story(name="Test Story2")
        ])
        su_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            su_token.access_token)

    def test_tasks_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual([], response)

    def test_create(self):
        self.post_json(self.resource, self.task_01)
        self.task_01['story_id'] = 2
        self.post_json(self.resource, self.task_01)

        # No filters here - we should receive both created tasks
        all_tasks = self.get_json(self.resource)
        self.assertEqual(2, len(all_tasks))

        # filter by story_id - we should receive only the one task
        tasks_story_10 = self.get_json(self.resource, story_id=1)
        self.assertEqual(1, len(tasks_story_10))
        self.assertEqual(self.task_01['title'], tasks_story_10[0]['title'])
