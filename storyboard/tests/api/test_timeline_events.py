# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from storyboard.common import event_types
from storyboard.tests import base


class TestTimelineEvents(base.FunctionalTest):

    def setUp(self):
        super(TestTimelineEvents, self).setUp()
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_get_all_events(self):
        """Assert that we can retrieve a list of events from a story."""

        response = self.get_json('/stories/1/events', expect_errors=True)

        # There should be three events.
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))

    def test_get_all_events_privacy(self):
        """Assert that events for private stories are access controlled."""

        url = '/stories/6/events'
        response = self.get_json(url, expect_errors=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))

        # The user with token `valid_user_token` can't see the story, and
        # so shouldn't be able to see the events
        headers = {'Authorization': 'Bearer valid_user_token'}
        response = self.get_json(url, headers=headers, expect_errors=True)
        self.assertEqual(0, len(response.json))

        # Unauthenticated users shouldn't be able to see anything in private
        # stories
        self.default_headers.pop('Authorization')
        response = self.get_json(url, expect_errors=True)
        self.assertEqual(0, len(response.json))

    def test_filter_by_event_type(self):
        """Assert that we can correctly filter an event by event type."""
        response = self.get_json('/stories/1/events?event_type=story_created'
                                 '&event_type=task_assignee_changed',
                                 expect_errors=True)

        # There should be two, and they must be one of the two selected event
        # types.
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        for event in response.json:
            if event['event_type'] not in ['story_created',
                                           'task_assignee_changed']:
                self.fail('Filtered result returned unexpected event type')

    def test_filter_by_invalid_event_type(self):
        """Assert that trying to filter by an invalid event type throws an
        acceptable exception.
        """
        response = self.get_json('/stories/1/events?event_type=invalid',
                                 expect_errors=True)

        # The request should error, and include all of our registered event
        # types in the result (to indicate a helpful error message.
        self.assertEqual(400, response.status_code)
        for type in event_types.ALL:
            if type not in response.json['faultstring']:
                self.fail('%s not found in error message' % (type,))
