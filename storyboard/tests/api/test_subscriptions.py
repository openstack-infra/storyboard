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


class TestSubscriptionsAsNobody(base.FunctionalTest):
    def setUp(self):
        super(TestSubscriptionsAsNobody, self).setUp()
        self.resource = '/subscriptions'

    def test_get_subscriptions(self):
        response = self.get_json(self.resource, expect_errors=True)
        self.assertEqual(401, response.status_code)


class TestSubscriptionsAsUser(base.FunctionalTest):
    def setUp(self):
        super(TestSubscriptionsAsUser, self).setUp()
        self.resource = '/subscriptions'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def test_get_subscriptions(self):
        """Assert that a base user has no subscriptions."""
        response = self.get_json(self.resource)
        self.assertEqual(0, len(response))

    def test_create_subscriptions(self):
        """Assert that we can create subscriptions."""
        response = self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project'
        })
        subscription = response.json

        self.assertEqual('project', subscription['target_type'])
        self.assertEqual(1, subscription['target_id'])
        self.assertEqual(2, subscription['user_id'])
        self.assertIsNotNone(subscription['id'])

        response2 = self.post_json(self.resource, {
            'user_id': 2,
            'target_id': 2,
            'target_type': 'project'
        })
        subscription2 = response2.json

        self.assertEqual('project', subscription2['target_type'])
        self.assertEqual(2, subscription2['target_id'])
        self.assertEqual(2, subscription2['user_id'])
        self.assertIsNotNone(subscription2['id'])

    def test_delete_subscriptions(self):
        """Assert that we can delete subscriptions."""
        response = self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project'
        })
        subscription = response.json

        search_response_1 = self.get_json(self.resource)
        self.assertEqual(1, len(search_response_1))

        response2 = self.delete(self.resource + '/' +
                                six.text_type(subscription['id']),
                                expect_errors=True)
        self.assertEqual(204, response2.status_code)

        search_response_2 = self.get_json(self.resource)
        self.assertEqual(0, len(search_response_2))

    def test_create_subscription_not_self(self):
        """Assert that a regular user cannot create a subscription for other
        people.
        """
        response = self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project',
            'user_id': 1
        }, expect_errors=True)
        self.assertEqual(403, response.status_code)

    def test_get_subscription(self):
        """Assert that we can read subscriptions. Note that the mock data has
        two subscriptions for the mock superuser, these should not show up
        here.
        """
        self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project'
        })

        response = self.get_json(self.resource)
        self.assertEqual(1, len(response))

        response = self.get_json(self.resource +
                                 '?target_type=project')
        self.assertEqual(1, len(response))

        response = self.get_json(self.resource +
                                 '?target_type=project&target_id=1')
        self.assertEqual(1, len(response))

        response = self.get_json(self.resource +
                                 '?target_type=story&target_id=1')
        self.assertEqual(0, len(response))

    def test_create_subscription_for_invalid_resource(self):
        """Assert that subscribing to something that doesn't exist is
        invalid.
        """
        response = self.post_json(self.resource, {
            'target_id': 100,
            'target_type': 'project'
        }, expect_errors=True)
        self.assertEqual(400, response.status_code)

        response = self.post_json(self.resource, {
            'target_id': 100,
            'target_type': 'story'
        }, expect_errors=True)
        self.assertEqual(400, response.status_code)

        response = self.post_json(self.resource, {
            'target_id': 100,
            'target_type': 'task'
        }, expect_errors=True)
        self.assertEqual(400, response.status_code)

        response = self.post_json(self.resource, {
            'target_id': 100,
            'target_type': 'notarealresource'
        }, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_cannot_create_duplicates(self):
        """Assert that we cannot create duplicate subscriptions."""
        response1 = self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project'
        })
        self.assertEqual(200, response1.status_code)
        response2 = self.post_json(self.resource, {
            'target_id': 1,
            'target_type': 'project'
        }, expect_errors=True)
        self.assertEqual(409, response2.status_code)

    def test_cannot_search_for_not_self(self):
        """Assert that we cannot search other people's subscriptions. Note
        that there are subscriptions in the mock data.
        """
        response = self.get_json(self.resource + '?user_id=1')
        self.assertEqual(0, len(response))


class TestSubscriptionsAsSuperuser(base.FunctionalTest):
    def setUp(self):
        super(TestSubscriptionsAsSuperuser, self).setUp()
        self.resource = '/subscriptions'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_get_subscriptions(self):
        """Assert that a base user has no subscriptions."""
        response = self.get_json(self.resource)
        self.assertEqual(3, len(response))

    def test_create_subscription_not_self(self):
        """Assert that we can create subscriptions for others."""
        response = self.post_json(self.resource, {
            'user_id': 3,
            'target_id': 1,
            'target_type': 'project'
        })
        subscription = response.json

        self.assertEqual('project', subscription['target_type'])
        self.assertEqual(1, subscription['target_id'])
        self.assertEqual(3, subscription['user_id'])
        self.assertIsNotNone(subscription['id'])

    def test_get_subscription(self):
        """Assert that we can read subscriptions for others.
        """
        response = self.get_json(self.resource + '/3')
        self.assertEqual(3, response['id'])
        self.assertEqual(3, response['user_id'])

    def test_can_search_for_not_self(self):
        """Assert that we can search other people's subscriptions."""
        response = self.get_json(self.resource + '?user_id=3')
        self.assertEqual(1, len(response))

    def test_delete_subscription_other(self):
        """Assert that we can delete subscriptions."""
        response = self.post_json(self.resource, {
            'user_id': 3,
            'target_id': 1,
            'target_type': 'project'
        })
        subscription = response.json

        search_response_1 = self.get_json(self.resource + '?user_id=3')
        self.assertEqual(2, len(search_response_1))

        response2 = self.delete(self.resource + '/' +
                                six.text_type(subscription['id']),
                                expect_errors=True)
        self.assertEqual(204, response2.status_code)

        search_response_2 = self.get_json(self.resource + '?user_id=3')
        self.assertEqual(1, len(search_response_2))
