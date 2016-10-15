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
        self.put_json(path, {'enable_login': False})
        user = self.get_json(path)
        self.assertFalse(user["enable_login"])


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
        self.put_json(path, {'enable_login': False})
        user = self.get_json(path)
        self.assertTrue(user["enable_login"])

    def test_malicious_update(self):
        # Preload the admin user.
        old_admin = self.get_json('/users/1')

        # Here we are posting to /user/2 with {id: 1, email:
        # 'omg@example.com'} to see if it allows us to update.
        response = self.put_json('/users/2',
                                 {
                                     'id': 1,
                                     'full_name': 'omg'
                                 },
                                 expect_errors=True)

        # Assert that the post was successful and that the PATH user was
        # updated.
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.json['id'])
        self.assertEqual('omg', response.json['full_name'])

        # Load the user which we've maliciously attempted to update.
        admin = self.get_json('/users/1')
        # Make certain that this user was not updated.
        self.assertEqual(old_admin, admin)

        # Load the user we should have actually updated.
        real_user = self.get_json('/users/2')
        # Make certain that this user was not updated.
        self.assertEqual(response.json, real_user)

    def test_self(self):
        result = self.get_json(self.resource + '/self')
        self.assertEqual(2, result['id'])


class TestSearchUsers(base.FunctionalTest):
    def setUp(self):
        super(TestSearchUsers, self).setUp()
        self.resource = '/users'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def testBrowse(self):
        result = self.get_json(self.resource + '?full_name=Regular')
        self.assertEqual(1, len(result))
