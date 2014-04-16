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

from storyboard.common import user_utils
from storyboard.tests import base


class TestTasks(base.FunctionalTest):

    def setUp(self):
        super(TestTasks, self).setUp()
        self.resource = '/tasks'

        self.task_01 = {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 10
        }

        self.original_user_utils = user_utils
        self.addCleanup(self._restore_user_utils)
        user_utils.username_by_id = lambda id: 'Test User'

    def _restore_user_utils(self):
        global user_utils
        user_utils = self.original_user_utils

    def test_tasks_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual([], response)

    def test_create(self):
        self.post_json(self.resource, self.task_01)
        self.task_01['story_id'] = 1000
        self.post_json(self.resource, self.task_01)

        # No filters here - we should receive both created tasks
        all_tasks = self.get_json(self.resource)
        self.assertEqual(2, len(all_tasks))

        # filter by story_id - we should receive only the one task
        tasks_story_10 = self.get_json(self.resource, story_id=10)
        self.assertEqual(1, len(tasks_story_10))
        self.assertEqual(self.task_01['title'], tasks_story_10[0]['title'])
