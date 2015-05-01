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

from oslo_config import cfg
from six.moves import http_client

import storyboard.common.exception as exc
from storyboard.tests import base


CONF = cfg.CONF


class OAuthExceptionTest(base.FunctionalTest):
    """Test for our OAuth Exceptions."""

    def test_error_names(self):
        """Assert that our various exceptions have the correct error code."""
        self.assertEqual('invalid_request',
                         exc.InvalidRequest.error)
        self.assertEqual('access_denied',
                         exc.AccessDenied.error)
        self.assertEqual('unsupported_response_type',
                         exc.UnsupportedResponseType.error)
        self.assertEqual('invalid_scope',
                         exc.InvalidScope.error)
        self.assertEqual('invalid_client',
                         exc.InvalidClient.error)
        self.assertEqual('unauthorized_client',
                         exc.UnauthorizedClient.error)
        self.assertEqual('invalid_grant',
                         exc.InvalidGrant.error)
        self.assertEqual('unsupported_grant_type',
                         exc.UnsupportedGrantType.error)
        self.assertEqual('server_error',
                         exc.ServerError.error)
        self.assertEqual('temporarily_unavailable',
                         exc.TemporarilyUnavailable.error)

    def test_redirect_uri_parsing(self):
        """Assert that the exception can automatically detect whether it can
        redirect.
        """

        invalid_uris = [
            None,
            'not_a_uri',
            'example.com/without/scheme',
            '/relative/uri',
            'gopher://example.com/not/http/scheme'
        ]

        for uri in invalid_uris:
            e = exc.OAuthException(redirect_uri=uri)
            self.assertIsNone(e.redirect_uri)
            self.assertEqual(http_client.BAD_REQUEST, e.code)

        valid_uris = [
            'http://example.com',
            'https://example.com',
            'https://example.com/',
            'https://example.com/foo/bar',
            'https://example.com/foo?uri=param',
            'https://example.com/foo?uri=param#fragment',
            'https://example.com/foo#fragment?fragment=param',
            'https://example.com/foo?uri=param#fragment?fragment=param',
            'https://example.com:1214/foo/bar'
        ]
        for uri in valid_uris:
            e = exc.OAuthException(redirect_uri=uri)
            self.assertEqual(uri, e.redirect_uri)
            self.assertEqual(http_client.SEE_OTHER, e.code)
