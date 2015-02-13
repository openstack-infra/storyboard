# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

from oslo.config import cfg

from storyboard.tests import base


CONF = cfg.CONF


class TestRedirectMiddleware(base.FunctionalTest):
    # Map of API -> Client urls that we're expecting.
    uri_mappings = {
        '/v1/projects': 'https://storyboard.openstack.org/#!/projects',
        '/v1/stories/22': 'https://storyboard.openstack.org/#!/stories/22',
        '/v1/project_groups/2': 'https://storyboard.openstack.org/'
                                '#!/project_groups/2'
    }

    def test_valid_results(self):
        """Assert that the expected URI mappings are returned."""
        headers = {
            'Accept': 'text/html;q=1'
        }

        for request_uri, redirect_uri in six.iteritems(self.uri_mappings):
            response = self.app.get(request_uri,
                                    headers=headers,
                                    expect_errors=True)

            self.assertEqual(303, response.status_code)
            self.assertEqual(redirect_uri, response.headers['Location'])

    def test_valid_results_as_post_put_delete(self):
        """Assert that POST, PUT, and DELETE methods are passed through to
        the API.
        """
        headers = {
            'Accept': 'text/html;q=1'
        }

        for request_uri, redirect_uri in six.iteritems(self.uri_mappings):
            response = self.app.post(request_uri, headers=headers,
                                     expect_errors=True)
            self.assertNotEqual(303, response.status_code)
            self.assertNotIn('Location', response.headers)

            response = self.app.put(request_uri, headers=headers,
                                    expect_errors=True)
            self.assertNotEqual(303, response.status_code)
            self.assertNotIn('Location', response.headers)

            response = self.app.delete(request_uri, headers=headers,
                                       expect_errors=True)
            self.assertNotEqual(303, response.status_code)
            self.assertNotIn('Location', response.headers)

    def test_graceful_accepts_header(self):
        """If the client prefers some other content type, make sure we
        respect that.
        """
        headers = {
            'Accept': 'text/html;q=.9,application/json;q=1'
        }

        for request_uri, redirect_uri in six.iteritems(self.uri_mappings):
            response = self.app.get(request_uri,
                                    headers=headers,
                                    expect_errors=True)

            self.assertNotEqual(303, response.status_code)
            self.assertNotIn('Location', response.headers)

    def test_with_browser_useragent(self):
        """Future protection test. Make sure that no other code accidentally
        gets in the way of browsers being redirected (such as search engine
        bot response handling). This is intended to be a canary for
        unexpected changes, rather than a comprehensive test for all possible
        browsers.
        """
        user_agents = [
            # Chrome 41
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML,'
            ' like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            # Firefox 36
            'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101'
            ' Firefox/36.0',
            # IE10
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0)'
            ' like Gecko'
        ]

        for request_uri, redirect_uri in six.iteritems(self.uri_mappings):

            for user_agent in user_agents:
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html;q=1'
                }

                response = self.app.get(request_uri,
                                        headers=headers,
                                        expect_errors=True)

                self.assertEqual(303, response.status_code)
                self.assertEqual(redirect_uri, response.headers['Location'])
