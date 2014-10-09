# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from storyboard.db.api import users as user_api
from storyboard.tests import base


class TestUsersAsSuperuser(base.FunctionalTest):
    def setUp(self):
        super(TestUsersAsSuperuser, self).setUp()
        self.resource = '/users'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_update_enable_login(self):
        path = self.resource + '/2'

        jenkins = self.get_json(path)
        self.assertIsNotNone(jenkins)

        # Try to modify the enable_login field
        jenkins['enable_login'] = False

        self.put_json(path, jenkins)
        user = user_api.user_get(user_id=2)
        self.assertFalse(user.enable_login)


class TestUsersAsUser(base.FunctionalTest):
    def setUp(self):
        super(TestUsersAsUser, self).setUp()
        self.resource = '/users'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def test_update_enable_login(self):
        path = self.resource + '/2'

        jenkins = self.get_json(path)
        self.assertIsNotNone(jenkins)

        # Try to modify the enable_login field
        jenkins['enable_login'] = False

        self.put_json(path, jenkins)
        user = user_api.user_get(user_id=2)
        self.assertTrue(user.enable_login)
