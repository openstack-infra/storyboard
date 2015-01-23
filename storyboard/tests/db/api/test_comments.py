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

from storyboard.db.api import comments
from storyboard.db.api import stories
from storyboard.tests.db import base


class CommentsTest(base.BaseDbTestCase):

    def setUp(self):
        super(CommentsTest, self).setUp()

        self.comment_01 = {
            'content': u'A comment',
            'story_id': 1
        }

        stories.story_create({"name": "Test Story"})

    def test_create_comment(self):
        self._test_create(self.comment_01, comments.comment_create)

    def test_update_comment(self):
        delta = {
            'content': u'An updated comment'
        }

        self._test_update(self.comment_01, delta,
                          comments.comment_create, comments.comment_update)
