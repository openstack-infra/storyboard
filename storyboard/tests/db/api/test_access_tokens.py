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

from datetime import datetime
import pytz

from storyboard.db.api import access_tokens
from storyboard.db.api import users
from storyboard.tests.db import base


class TokenTest(base.BaseDbTestCase):

    def setUp(self):
        super(TokenTest, self).setUp()

        self.token_01 = {
            "access_token": u'an_access_token',
            "expires_in": 3600,
            "expires_at": datetime.now(pytz.utc),
            "user_id": 1
        }

        users.user_create({"fullname": "Test User"})

    def test_get_existing_token(self):
        self.assertIsNotNone(
            access_tokens.access_token_get_by_token("valid_user_token"))

    def test_get_by_prefix(self):
        # This test checks that a token is not fetch by LIKE comparison
        self.assertIsNone(
            access_tokens.access_token_get_by_token("valid_user_t"))

    def test_get_not_existing(self):
        self.assertIsNone(
            access_tokens.access_token_get_by_token("not_a_token"))

    def test_create_token(self):
        self._test_create(self.token_01, access_tokens.access_token_create)

    def test_delete_token(self):
        created_token = access_tokens.access_token_create(self.token_01)

        self.assertIsNotNone(created_token, "Could not create a Token")

        access_tokens.access_token_delete_by_token(created_token.access_token)

        fetched_token = access_tokens.access_token_get_by_token(
            created_token.access_token)
        self.assertIsNone(fetched_token, "A deleted token was fetched.")
