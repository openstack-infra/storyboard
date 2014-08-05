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
from storyboard.db.models import User
from storyboard.tests import base


class TestUsersAsSuperuser(base.FunctionalTest):
    def setUp(self):
        super(TestUsersAsSuperuser, self).setUp()
        self.resource = '/users'

        self.load_data([
            User(id=1,
                 username='superuser',
                 email='superuser@example.com',
                 full_name='Super User',
                 is_superuser=True),
            User(id=2,
                 username='jenkins',
                 email='jenkins@example.com',
                 full_name='Jenkins User',
                 is_superuser=False,
                 enable_login=False)
        ])
        su_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            su_token.access_token)

    def test_update_enable_login(self):
        path = self.resource + '/2'

        jenkins = self.get_json(path)
        self.assertIsNotNone(jenkins)

        # Try to modify the enable_login field
        jenkins['enable_login'] = True

        self.put_json(path, jenkins)
        user = user_api.user_get(user_id=2)
        self.assertTrue(user.enable_login)


class TestUsersAsUser(base.FunctionalTest):
    def setUp(self):
        super(TestUsersAsUser, self).setUp()
        self.resource = '/users'

        self.load_data([
            User(id=1,
                 username='user',
                 email='user@example.com',
                 full_name='User',
                 is_superuser=False,
                 enable_login=False),
        ])
        active_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            active_token.access_token)

    def test_update_enable_login(self):
        path = self.resource + '/1'

        jenkins = self.get_json(path)
        self.assertIsNotNone(jenkins)

        # Try to modify the enable_login field
        jenkins['enable_login'] = True

        self.put_json(path, jenkins)
        user = user_api.user_get(user_id=1)
        self.assertFalse(user.enable_login)
