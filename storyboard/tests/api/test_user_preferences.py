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


class TestUserPreferencesAsUser(base.FunctionalTest):
    def setUp(self):
        super(TestUserPreferencesAsUser, self).setUp()
        self.resource = '/users/2/preferences'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def test_simple_get(self):
        """This test asserts that the preferences controller comes back with
        'something'. Individual plugins should make sure that their own
        preferences work properly.
        """
        response = self.get_json(self.resource)
        self.assertEqual({}, response)

    def test_simple_post(self):
        """This test asserts that the client can add override entire key/value
        pairs on the preferences hash.
        """
        preferences = {
            'intPref': 1,
            'boolPref': True,
            'floatPref': 1.23,
            'stringPref': 'oh hai'
        }

        response = self.post_json(self.resource, preferences)
        self.assertEqual(response.json['intPref'],
                         preferences['intPref'])
        self.assertEqual(response.json['boolPref'],
                         preferences['boolPref'])
        self.assertEqual(response.json['floatPref'],
                         preferences['floatPref'])
        self.assertEqual(response.json['stringPref'],
                         preferences['stringPref'])

    def test_remove_preference(self):
        """Assert that a user may remove individual preferences.
        """

        # Pre save some prefs.
        self.post_json(self.resource, {
            'foo': 'bar',
            'intPref': 1,
            'boolPref': True,
            'floatPref': 1.23,
            'stringPref': 'oh hai'
        })

        response = self.get_json(self.resource)
        self.assertTrue(response['boolPref'])
        self.assertEqual(1, response['intPref'])
        self.assertTrue('oh hai', response['stringPref'])
        self.assertTrue('bar', response['foo'])

        self.post_json(self.resource, {
            'foo': 'fizz',
            'intPref': None,
            'boolPref': None,
            'stringPref': None,
            'floatPref': None
        })

        response = self.get_json(self.resource)
        self.assertEqual('fizz', response['foo'])
        self.assertFalse(hasattr(response, 'intPref'))
        self.assertFalse(hasattr(response, 'stringPref'))
        self.assertFalse(hasattr(response, 'boolPref'))

    def test_get_unauthorized(self):
        """This test asserts that the preferences controller comes back with
        'something'. Individual plugins should make sure that their own
        preferences work properly.
        """
        response = self.get_json('/users/1/preferences', expect_errors=True)
        self.assertEqual(403, response.status_code)


class TestUserPreferencesAsNoUser(base.FunctionalTest):
    def setUp(self):
        super(TestUserPreferencesAsNoUser, self).setUp()
        self.resource = '/users/2/preferences'

    def test_simple_get(self):
        """This test asserts that the preferences controller comes back with
        'something'. Individual plugins should make sure that their own
        preferences work properly.
        """
        response = self.get_json(self.resource, expect_errors=True)
        self.assertEqual(401, response.status_code)
