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
from storyboard.tests.db import base


class StoriesTest(base.BaseDbTestCase):

    def setUp(self):
        super(StoriesTest, self).setUp()

        self.story_01 = {
            'title': u'Worst Story Ever',
            'description': u'Story description'
        }

    def test_create_story(self):
        self._test_create(self.story_01, stories.story_create)

    def test_update_story(self):
        delta = {
            'title': u'New Title',
            'description': u'New Description'
        }
        self._test_update(self.story_01, delta,
                          stories.story_create, stories.story_update)
