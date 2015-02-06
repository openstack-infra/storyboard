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

from storyboard.db.api import auth_codes
from storyboard.db.api import users
from storyboard.tests.db import base


class AuthorizationCodeTest(base.BaseDbTestCase):

    def setUp(self):
        super(AuthorizationCodeTest, self).setUp()

        self.code_01 = {
            'code': u'some_random_stuff',
            'state': u'another_random_stuff',
            'user_id': 1
        }

        users.user_create({"fullname": "Test User"})

    def test_create_code(self):
        self._test_create(self.code_01, auth_codes.authorization_code_save)

    def test_delete_code(self):
        created_code = auth_codes.authorization_code_save(self.code_01)

        self.assertIsNotNone(created_code,
                             "Could not create an Authorization code")

        auth_codes.authorization_code_delete(created_code.code)

        fetched_code = auth_codes.authorization_code_get(created_code.code)
        self.assertIsNone(fetched_code)
