# -*- coding: utf-8 -*-

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

"""
test_storyboard
----------------------------------

Tests for `storyboard` module.
"""
import copy
import json

from mock import patch

from storyboard.tests.api.utils import FakeSession
from storyboard.tests import base

SAMPLE_STORY = {
    "title": "test_story",
    "description": "some description"
}

SAMPLE_STORY_REQUEST = {
    "story": SAMPLE_STORY
}


class TestStories(base.FunctionalTest):

    @patch("storyboard.openstack.common.db.sqlalchemy.session.get_session")
    def test_stories_endpoint(self, session_mock):
        fake_session = FakeSession()
        session_mock.return_value = fake_session

        response = self.get_json(path="/stories")
        self.assertEqual([], response)

    @patch("storyboard.openstack.common.db.sqlalchemy.session.get_session")
    def test_create(self, session_mock):
        fake_session = FakeSession()
        session_mock.return_value = fake_session

        response = self.post_json("/stories", SAMPLE_STORY_REQUEST)
        story = json.loads(response.body)

        self.assertIn("id", story)
        self.assertIn("created_at", story)
        self.assertEqual(story["title"], SAMPLE_STORY["title"])
        self.assertEqual(story["description"], SAMPLE_STORY["description"])

    @patch("storyboard.openstack.common.db.sqlalchemy.session.get_session")
    def test_update(self, session_mock):
        fake_session = FakeSession()
        session_mock.return_value = fake_session

        response = self.post_json("/stories", SAMPLE_STORY_REQUEST)
        old_story = json.loads(response.body)

        update_request = copy.deepcopy(SAMPLE_STORY_REQUEST)
        update_request["story_id"] = old_story["id"]
        update_request["story"]["title"] = "updated_title"
        update_request["story"]["description"] = "updated_description"

        response = self.put_json("/stories", update_request)
        updated_story = json.loads(response.body)

        self.assertEqual(updated_story["id"], old_story["id"])
        self.assertEqual(updated_story["created_at"], old_story["created_at"])

        self.assertNotEqual(updated_story["title"], old_story["title"])
        self.assertNotEqual(updated_story["description"],
                            old_story["description"])
