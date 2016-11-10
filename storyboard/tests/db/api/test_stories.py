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

from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api
from storyboard.tests.db import base


class StoriesTest(base.BaseDbTestCase):

    def setUp(self):
        super(StoriesTest, self).setUp()

        self.story_01 = {
            'title': u'Worst Story Ever',
            'description': u'Story description'
        }

    def test_create_story(self):
        self._test_create(self.story_01, stories_api.story_create)

    def test_update_story(self):
        delta = {
            'title': u'New Title',
            'description': u'New Description'
        }
        self._test_update(self.story_01, delta,
                          stories_api.story_create, stories_api.story_update)

    def test_delete_story(self):
        # This test uses mock_data
        story_id = 1
        # Verify that we can look up a story with tasks and events
        story = stories_api.story_get_simple(story_id)
        self.assertIsNotNone(story)
        tasks = tasks_api.task_get_all(story_id=story_id)
        self.assertEqual(len(tasks), 3)
        task_ids = [t.id for t in tasks]
        events = events_api.events_get_all(story_id=story_id)
        self.assertEqual(len(events), 3)
        event_ids = [e.id for e in events]

        # Delete the story
        stories_api.story_delete(story_id)
        story = stories_api.story_get_simple(story_id)
        self.assertIsNone(story)
        # Verify that the story's tasks were deleted
        tasks = tasks_api.task_get_all(story_id=story_id)
        self.assertEqual(len(tasks), 0)
        for tid in task_ids:
            task = tasks_api.task_get(task_id=tid)
            self.assertIsNone(task)
        # And the events
        events = events_api.events_get_all(story_id=story_id)
        self.assertEqual(len(events), 0)
        for eid in event_ids:
            event = events_api.event_get(event_id=eid)
            self.assertIsNone(event)
