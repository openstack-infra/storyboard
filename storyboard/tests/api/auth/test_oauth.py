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

from urlparse import parse_qs
from urlparse import urlparse
import uuid

from oslo.config import cfg
import six

from storyboard.db.api import access_tokens as token_api
from storyboard.db.api import auth as auth_api
from storyboard.tests import base


CONF = cfg.CONF


class BaseOAuthTest(base.FunctionalTest):
    """Base functional test class, including reusable assertions."""

    def assertValidRedirect(self, response, redirect_uri,
                            expected_status_code, **kwargs):
        """Validate a redirected error response. All the URL components should
        match the original redirect_uri, with the exception of the parameters,
        which should contain an 'error' and an 'error_description' field of
        the provided types.

        :param redirect_uri: The expected redirect_uri
        :param response: The raw HTTP response.
        :param expected_status_code: The expected status code.
        :param kwargs: Parameters expected in the URI parameters.
        :return:
        """

        self.assertEqual(expected_status_code, response.status_code)
        # Split the url into parts.
        location = response.headers.get('Location')
        location_url = urlparse(location)
        parameters = parse_qs(location_url[4])

        # Break out the redirect uri to compare and make sure we're headed
        # back to the redirect URI with the appropriate error codes.
        configured_url = urlparse(redirect_uri)
        self.assertEqual(configured_url[0], location_url[0])
        self.assertEqual(configured_url[1], location_url[1])
        self.assertEqual(configured_url[2], location_url[2])
        self.assertEqual(configured_url[3], location_url[3])
        # 4 is ignored, it contains new parameters.
        self.assertEqual(configured_url[5], location_url[5])

        # Make sure we have the correct error response.
        self.assertEqual(len(kwargs), len(parameters))
        for key, value in six.iteritems(kwargs):
            self.assertIn(key, parameters)
            self.assertIsNotNone(parameters[key])
            self.assertEqual(value, parameters[key][0])


class TestOAuthAuthorize(BaseOAuthTest):
    """Functional tests for our /oauth/authorize endpoint. For more
    information, please see here: http://tools.ietf.org/html/rfc6749

    This is not yet a comprehensive test of this endpoint, though it hits
    the major error cases. Additional work as follows:

    * Test that including a request parameter more than once results in
    invalid_request
    * Test that server errors return with error_description="server_error"
    """

    valid_params = {
        'response_type': 'code',
        'client_id': 'storyboard.openstack.org',
        'redirect_uri': 'https://storyboard.openstack.org/#!/auth/token',
        'scope': 'user'
    }

    def test_valid_authorize_request(self):
        """This test ensures that the authorize request against the oauth
        endpoint succeeds with expected values.
        """

        random_state = six.text_type(uuid.uuid4())

        # Simple GET with various parameters
        response = self.get_json(path='/openid/authorize',
                                 expect_errors=True,
                                 state=random_state,
                                 **self.valid_params)

        # Assert that this is a redirect response
        self.assertEqual(303, response.status_code)

        # Assert that the redirect request goes to launchpad.
        location = response.headers.get('Location')
        location_url = urlparse(location)
        parameters = parse_qs(location_url[4])

        # Check the URL
        conf_openid_url = CONF.oauth.openid_url
        self.assertEqual(conf_openid_url, location[0:len(conf_openid_url)])

        # Check OAuth Registration parameters
        self.assertIn('fullname', parameters['openid.sreg.required'][0])
        self.assertIn('email', parameters['openid.sreg.required'][0])
        self.assertIn('nickname', parameters['openid.sreg.required'][0])

        # Check redirect URL
        redirect = parameters['openid.return_to'][0]
        redirect_url = urlparse(redirect)
        redirect_params = parse_qs(redirect_url[4])

        self.assertIn('/openid/authorize_return', redirect)
        self.assertEqual(random_state,
                         redirect_params['state'][0])
        self.assertEqual(self.valid_params['redirect_uri'],
                         redirect_params['sb_redirect_uri'][0])

    def test_authorize_invalid_response_type(self):
        """Assert that an invalid response_type redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        invalid_params['response_type'] = 'invalid_code'

        # Simple GET with invalid code parameters
        random_state = six.text_type(uuid.uuid4())
        response = self.get_json(path='/openid/authorize',
                                 expect_errors=True,
                                 state=random_state,
                                 **invalid_params)

        # Validate the error response
        self.assertValidRedirect(response=response,
                                 expected_status_code=302,
                                 redirect_uri=invalid_params['redirect_uri'],
                                 error='unsupported_response_type',
                                 error_description='response_type must be '
                                                   '\'code\'')


class TestOAuthAccessToken(BaseOAuthTest):
    """Functional test for the /oauth/token endpoint for the generation of
    access tokens.
    """

    def test_valid_access_request(self):
        """This test ensures that the access token request may execute
        properly with a valid token.
        """

        # Generate a valid auth token
        authorization_code = auth_api.authorization_code_save({
            'user_id': 2,
            'state': 'test_state',
            'code': 'test_valid_code'
        })

        # POST with content: application/x-www-form-urlencoded
        response = self.app.post('/v1/openid/token',
                                 params={
                                     'code': authorization_code.code,
                                     'grant_type': 'authorization_code'
                                 },
                                 content_type=
                                 'application/x-www-form-urlencoded',
                                 expect_errors=True)

        # Assert that this is a successful response
        self.assertEqual(200, response.status_code)

        # Assert that the token came back in the response
        token = response.json
        self.assertIsNotNone(token['access_token'])
        self.assertIsNotNone(token['expires_in'])
        self.assertIsNotNone(token['id_token'])
        self.assertIsNotNone(token['refresh_token'])
        self.assertIsNotNone(token['token_type'])
        self.assertEqual('Bearer', token['token_type'])

        # Assert that the access token is in the database
        access_token = \
            token_api.access_token_get_by_token(token['access_token'])
        self.assertIsNotNone(access_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEquals(2, access_token.user_id)
        self.assertEquals(token['id_token'], access_token.user_id)
        self.assertEqual(token['expires_in'], CONF.oauth.access_token_ttl)
        self.assertEqual(token['expires_in'], access_token.expires_in)
        self.assertEqual(token['access_token'], access_token.access_token)

        # Assert that the refresh token is in the database
        refresh_token = \
            auth_api.refresh_token_get(token['refresh_token'])
        self.assertIsNotNone(refresh_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEquals(2, refresh_token.user_id)
        self.assertEqual(CONF.oauth.refresh_token_ttl,
                         refresh_token.expires_in)
        self.assertEqual(token['refresh_token'], refresh_token.refresh_token)

        # Assert that the authorization code is no longer in the database.
        self.assertIsNone(auth_api.authorization_code_get(
            authorization_code.code
        ))
