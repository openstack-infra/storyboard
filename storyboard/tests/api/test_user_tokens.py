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

import six

from storyboard.tests import base


class TestUserTokensAsUser(base.FunctionalTest):
    def setUp(self):
        super(TestUserTokensAsUser, self).setUp()
        self.resource = '/users/2/tokens'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def test_browse(self):
        """Assert a basic browse for your own tokens.
        """
        response = self.get_json(self.resource, expect_errors=True)
        self.assertEqual(200, response.status_code)

    def test_unauthorized_browse(self):
        """Assert a basic browse for someone else's tokens
        """
        response = self.get_json('/users/1/tokens', expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_get_empty(self):
        """Assert that a user may get an empty record and receive a 404
        response.
        """
        response = self.get_json(self.resource + '/99', expect_errors=True)
        self.assertEqual(404, response.status_code)

    def test_simple_create_and_retrieve(self):
        """Assert that a user may create tokens for themselves."""
        token = {
            'user_id': 2,
            'expires_in': 3600,
            'access_token': 'test_token'
        }

        response = self.post_json(self.resource, token)
        self.assertEqual(response.json['user_id'], 2)
        self.assertEqual(response.json['expires_in'], 3600)
        self.assertEqual(response.json['access_token'], 'test_token')
        self.assertIsNotNone(response.json['id'])

        read_response = self.get_json(self.resource + '/' +
                                      six.text_type(response.json['id']))

        self.assertEqual(response.json['user_id'],
                         read_response['user_id'])
        self.assertEqual(response.json['expires_in'],
                         read_response['expires_in'])
        self.assertEqual(response.json['access_token'],
                         read_response['access_token'])
        self.assertIsNotNone(response.json['id'],
                             read_response['id'])

    def test_delete_all_user_tokens(self):
        """Assert that user may delete all his tokens
        """
        resource = self.resource + "/delete_all"
        self.delete(resource)

        response = self.get_json(self.resource, expect_errors=True)
        self.assertEqual(401, response.status_code)

    def test_create_access_token_autofill(self):
        """Assert that creating a token without the access_token parameter
        generates a randomly generated access token.
        """
        token = {
            'user_id': 2,
            'expires_in': 3600
        }

        response = self.post_json(self.resource, token)
        self.assertEqual(response.json['user_id'], 2)
        self.assertEqual(response.json['expires_in'], 3600)
        self.assertIsNotNone(response.json['access_token'])
        self.assertTrue(len(response.json['access_token']) > 10)
        self.assertIsNotNone(response.json['id'])

    def test_cannot_create_duplicate_token(self):
        """Assert that a user may not violate the uniqueness constraint on user
        tokens.
        """
        token = {
            'user_id': 2,
            'expires_in': 3600,
            'access_token': 'valid_user_token'
        }

        response = self.post_json(self.resource, token, expect_errors=True)
        self.assertEqual(409, response.status_code)

    def test_update_expiration_date(self):
        """Assert that a user may ONLY update the expiration time on their
        own tokens.
        """
        token = {
            'user_id': 2,
            'expires_in': 3600
        }

        response = self.post_json(self.resource, token)
        self.assertEqual(response.json['expires_in'], 3600)
        self.assertIsNotNone(response.json['access_token'])
        self.assertIsNotNone(response.json['id'])

        new_record = response.json.copy()

        new_record['expires_in'] = 3601

        updated = self.put_json(self.resource + '/' +
                                six.text_type(response.json['id']),
                                new_record, expect_errors=True)

        self.assertEqual(updated.json['expires_in'], 3601)

    def test_delete_token(self):
        """Assert that a user may delete their own user tokens."""
        token = {
            'user_id': 2,
            'expires_in': 3600
        }

        response = self.post_json(self.resource, token)
        self.assertEqual(response.json['expires_in'], 3600)
        self.assertIsNotNone(response.json['access_token'])
        self.assertIsNotNone(response.json['id'])

        response = self.delete(self.resource + '/' +
                               six.text_type(response.json['id']),
                               expect_errors=True)
        self.assertEqual(204, response.status_code)

    def test_create_unauthorized(self):
        """Assert that a user cannot create a token for someone else."""
        token = {
            'user_id': 3,
            'expires_in': 3600
        }

        response = self.post_json('/users/3/tokens', token, expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_get_unauthorized(self):
        """Assert that a user cannot retrieve a token for someone else."""
        response = self.get_json('/users/1/tokens/1', expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_update_unauthorized(self):
        """Assert that a user cannot update a token for someone else."""
        token = {
            'user_id': 1,
            'expires_in': 3601
        }

        response = self.put_json('/users/1/tokens/1', token,
                                 expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_delete_unauthorized(self):
        """Assert that a user cannot delete a token for someone else."""

        response = self.delete('/users/1/tokens/1', expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_funny_business(self):
        """Assert that a user cannot create a token for someone else by
        swapping the ID in the payload while still accessing their own user
        id rest endpoint.
        """
        token = {
            'user_id': 3,
            'expires_in': 3600
        }

        response = self.post_json(self.resource, token, expect_errors=True)
        self.assertEqual(403, response.status_code)


class TestUserTokensAsNoUser(base.FunctionalTest):
    def setUp(self):
        super(TestUserTokensAsNoUser, self).setUp()
        self.resource = '/users/2/tokens'

    def test_unauthorized_browse(self):
        """Assert a basic browse for someone else's tokens.
        """
        response = self.get_json('/users/1/tokens', expect_errors=True)
        self.assertEqual(401, response.status_code)

    def test_create_unauthorized(self):
        """Assert that a user cannot create a token for someone else."""
        token = {
            'user_id': 3,
            'expires_in': 3600
        }

        response = self.post_json('/users/3/tokens', token, expect_errors=True)
        self.assertEqual(401, response.status_code)

    def test_get_unauthorized(self):
        """Assert that a user cannot retrieve a token for someone else."""
        response = self.get_json('/users/1/tokens/1', expect_errors=True)
        self.assertEqual(401, response.status_code)

    def test_update_unauthorized(self):
        """Assert that a user cannot update a token for someone else."""
        token = {
            'user_id': 1,
            'expires_in': 3601
        }

        response = self.put_json('/users/1/tokens/1', token,
                                 expect_errors=True)
        self.assertEqual(401, response.status_code)

    def test_delete_unauthorized(self):
        """Assert that a user cannot delete a token for someone else."""

        response = self.delete('/users/1/tokens/1', expect_errors=True)
        self.assertEqual(401, response.status_code)


class TestUserTokensAsSuperuser(base.FunctionalTest):
    def setUp(self):
        super(TestUserTokensAsSuperuser, self).setUp()
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_other_browse(self):
        """Assert a basic browse for someone else's tokens.
        """
        response = self.get_json('/users/2/tokens', expect_errors=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.json), 2)

    def test_create_other(self):
        """Assert that a superuser CAN create a token for someone else."""
        token = {
            'user_id': 3,
            'expires_in': 3600,
            'access_token': 'test_token'
        }

        response = self.post_json('/users/3/tokens', token)
        self.assertEqual(response.json['user_id'], 3)
        self.assertEqual(response.json['expires_in'], 3600)
        self.assertEqual(response.json['access_token'], 'test_token')
        self.assertIsNotNone(response.json['id'])

    def test_get_other(self):
        """Assert that a superuser CAN retrieve a token for someone else."""
        response = self.get_json('/users/2/tokens/3', expect_errors=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.json['user_id'])
        self.assertEqual('valid_user_token', response.json['access_token'])

    def test_update_other(self):
        """Assert that a superuser CAN update a token for someone else."""
        response = self.get_json('/users/2/tokens/3', expect_errors=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.json['user_id'])
        self.assertEqual('valid_user_token', response.json['access_token'])

        new_record = response.json.copy()
        new_record['expires_in'] = 3601
        put_response = self.put_json('/users/2/tokens/3', new_record,
                                     expect_errors=True)
        self.assertEqual(200, put_response.status_code)
        self.assertEqual(2, put_response.json['user_id'])
        self.assertEqual(3601, put_response.json['expires_in'])

    def test_delete_other(self):
        """Assert that a superuser CAN delete a token for someone else."""
        response = self.delete('/users/2/tokens/3', expect_errors=True)
        self.assertEqual(204, response.status_code)

        response = self.get_json('/users/2/tokens/3', expect_errors=True)
        self.assertEqual(404, response.status_code)
