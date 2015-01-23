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

from storyboard.db.api import stories
from storyboard.db.api import tasks
from storyboard.db.api import users
from storyboard.tests.db import base


class TasksTest(base.BaseDbTestCase):

    def setUp(self):
        super(TasksTest, self).setUp()

        self.task_01 = {
            'title': u'Invent time machine',
            'status': 'todo',
            'story_id': 1
        }

        stories.story_create({"name": "Test Story"})
        users.user_create({"fullname": "Test User"})

    def test_create_task(self):
        self._test_create(self.task_01, tasks.task_create)

    def test_update_task(self):
        delta = {
            'status': 'review',
            'assignee_id': 1
        }

        self._test_update(self.task_01, delta,
                          tasks.task_create, tasks.task_update)
