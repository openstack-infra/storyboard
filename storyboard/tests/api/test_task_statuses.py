# Copyright (c) 2014 Mirantis Inc.
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

import six.moves.urllib.parse as urlparse

from storyboard.tests import base


class TestTaskStatusesSearch(base.FunctionalTest):
    """Test the Task Status endpoint."""

    def setUp(self):
        super(TestTaskStatusesSearch, self).setUp()

    def build_search_url(self, params=None, raw=''):
        if params:
            raw = urlparse.urlencode(params)
        return '/task_statuses?%s' % raw

    def test_search(self):
        """Test a basic search."""
        url = self.build_search_url({
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

    def test_search_by_name(self):
        """Test searching by various names."""

        # Assert that searching by parts of names works.
        url = self.build_search_url({
            'name': 'inval'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        # Assert that searching by 'task status' or some permutation works.
        url = self.build_search_url({
            'name': 'task'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        url = self.build_search_url({
            'name': 'stat'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

    def test_search_constrain(self):
        """Test constraint searches."""
        url = self.build_search_url({
            'limit': 2
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Limit'])
        self.assertEqual('5', results.headers['X-Total'])
