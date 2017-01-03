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

import datetime
import os
import pytz
import requests
import uuid

from mock import patch
from oslo_config import cfg
import six
import six.moves.urllib.parse as urlparse

from storyboard.api.auth import ErrorMessages as e_msg
from storyboard.db.api import access_tokens as token_api
from storyboard.db.api import auth_codes as auth_api
from storyboard.db.api import refresh_tokens
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
        location_url = urlparse.urlparse(location)
        parameters = urlparse.parse_qs(location_url[4])

        # Break out the redirect uri to compare and make sure we're headed
        # back to the redirect URI with the appropriate error codes.
        configured_url = urlparse.urlparse(redirect_uri)
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
        location_url = urlparse.urlparse(location)
        parameters = urlparse.parse_qs(location_url[4])

        # Check the URL
        conf_openid_url = CONF.oauth.openid_url
        self.assertEqual(conf_openid_url, location[0:len(conf_openid_url)])

        # Check OAuth Registration parameters
        self.assertIn('fullname', parameters['openid.sreg.required'][0])
        self.assertIn('email', parameters['openid.sreg.required'][0])

        # Check redirect URL
        redirect = parameters['openid.return_to'][0]
        redirect_url = urlparse.urlparse(redirect)
        redirect_params = urlparse.parse_qs(redirect_url[4])

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
                                 error_description=e_msg.INVALID_RESPONSE_TYPE)

    def test_authorize_no_response_type(self):
        """Assert that an nonexistent response_type redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        del invalid_params['response_type']

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
                                 error_description=e_msg.NO_RESPONSE_TYPE)

    def test_authorize_no_client(self):
        """Assert that a nonexistent client redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        del invalid_params['client_id']

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
                                 error='invalid_client',
                                 error_description=e_msg.NO_CLIENT_ID)

    def test_authorize_invalid_client(self):
        """Assert that an invalid client redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        invalid_params['client_id'] = 'invalid_client'

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
                                 error='unauthorized_client',
                                 error_description=e_msg.INVALID_CLIENT_ID)

    def test_authorize_invalid_scope(self):
        """Assert that an invalid scope redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        invalid_params['scope'] = 'invalid_scope'

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
                                 error='invalid_scope',
                                 error_description=e_msg.INVALID_SCOPE)

    def test_authorize_no_scope(self):
        """Assert that a nonexistent scope redirects back to the
        redirect_uri and provides the expected error response.
        """
        invalid_params = self.valid_params.copy()
        del invalid_params['scope']

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
                                 error='invalid_scope',
                                 error_description=e_msg.NO_SCOPE)

    def test_authorize_invalid_redirect_uri(self):
        """Assert that an invalid redirect_uri returns a 400 message with the
        appropriate error message encoded in the body of the response.
        """
        invalid_params = self.valid_params.copy()
        invalid_params['redirect_uri'] = 'not_a_valid_uri'

        # Simple GET with invalid code parameters
        random_state = six.text_type(uuid.uuid4())
        response = self.get_json(path='/openid/authorize',
                                 expect_errors=True,
                                 state=random_state,
                                 **invalid_params)

        # Assert that this is NOT a redirect
        self.assertEqual(400, response.status_code)
        self.assertIsNotNone(response.json)
        self.assertEqual('invalid_request', response.json['error'])
        self.assertEqual(e_msg.INVALID_REDIRECT_URI,
                         response.json['error_description'])

    def test_authorize_no_redirect_uri(self):
        """Assert that a nonexistent redirect_uri returns a 400 message with
        the appropriate error message encoded in the body of the response.
        """
        invalid_params = self.valid_params.copy()
        del invalid_params['redirect_uri']

        # Simple GET with invalid code parameters
        random_state = six.text_type(uuid.uuid4())
        response = self.get_json(path='/openid/authorize',
                                 expect_errors=True,
                                 state=random_state,
                                 **invalid_params)

        # Assert that this is NOT a redirect
        self.assertEqual(400, response.status_code)
        self.assertIsNotNone(response.json)
        self.assertEqual('invalid_request', response.json['error'])
        self.assertEqual(e_msg.NO_REDIRECT_URI,
                         response.json['error_description'])


@patch.object(requests, 'post')
class TestOAuthAuthorizeReturn(BaseOAuthTest):
    """Functional tests for our /oauth/authorize_return, which handles
    responses from the launchpad service. The expected behavior here is that
    a successful response will 303 back to the client in accordance with
    the OAuth Authorization Response as described here:
    http://tools.ietf.org/html/rfc6749#section-4.1.2

    Errors from launchpad should be recast into the appropriate error code
    and follow the error responses in the same section.
    """
    valid_params = {
        'response_type': 'code',
        'client_id': 'storyboard.openstack.org',
        'sb_redirect_uri': 'https://storyboard.openstack.org/!#/auth/token',
        'scope': 'user',
        'openid.assoc_handle': '{HMAC-SHA1}{54d11f3f}{lmmpZg==}',
        'openid.ax.count.Email': 0,
        'openid.ax.type.Email': 'http://schema.openid.net/contact/email',
        'openid.ax.count.FirstName': 0,
        'openid.ax.type.FirstName': 'http://schema.openid.net/namePerson'
                                    '/first',
        'openid.ax.count.LastName': 0,
        'openid.ax.type.LastName': 'http://schema.openid.net/namePerson'
                                   '/last',
        'openid.ax.mode': 'fetch_response',

        # These two would usually be the OpenID URI.
        'openid.claimed_id': 'regularuser_openid',
        'openid.identity': 'regularuser_openid',

        'openid.mode': 'id_res',
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.ns.ax": "http://openid.net/srv/ax/1.0",
        "openid.ns.sreg": "http://openid.net/sreg/1.0",
        "openid.op_endpoint": "https://login.launchpad.net/+openid",
        "openid.response_nonce": "2015-02-03T19:19:27ZY5SIfO",
        "openid.return_to": "https://storyboard.openstack.org/api/v1/openid"
                            "/authorize_return?scope=user",
        "openid.sig=2ghVIBuCYDFe32cMOvY9rTCsQfg": "",
        "openid.signed": "assoc_handle,ax.count.Email,ax.count.FirstName,"
                         "ax.count.LastName,ax.mode,ax.type.Email,"
                         "ax.type.FirstName,ax.type.LastName,claimed_id,"
                         "identity,mode,ns,ns.ax,ns.sreg,op_endpoint,"
                         "response_nonce,return_to,signed,sreg.email,"
                         "sreg.fullname",
        "openid.sreg.email": "test@example.com",
        "openid.sreg.fullname": "Test User",
    }

    def _mock_response(self, mock_post, valid=True):
        """Set the mock response from the openid endpoint to either true or
        false.

        :param mock_post: The mock to decorate.
        :param valid: Whether to provide a valid or invalid response.
        :return:
        """

        mock_post.return_value.status_code = 200
        if valid:
            mock_post.return_value.content = \
                'is_valid:true\nns:http://specs.openid.net/auth/2.0\n'
        else:
            mock_post.return_value.content = \
                'is_valid:false\nns:http://specs.openid.net/auth/2.0\n'

    def test_valid_response_request(self, mock_post):
        """This test ensures that the authorize request against the oauth
        endpoint succeeds with expected values.
        """
        self._mock_response(mock_post, valid=True)

        random_state = six.text_type(uuid.uuid4())

        # Simple GET with various parameters
        response = self.get_json(path='/openid/authorize_return',
                                 expect_errors=True,
                                 state=random_state,
                                 **self.valid_params)

        # Try to pull the code out of the response
        location = response.headers.get('Location')
        location_url = urlparse.urlparse(location)
        parameters = urlparse.parse_qs(location_url[4])

        with base.HybridSessionManager():
            token = auth_api.authorization_code_get(parameters['code'])

        redirect_uri = self.valid_params['sb_redirect_uri']
        # Validate the redirect response
        self.assertValidRedirect(response=response,
                                 expected_status_code=302,
                                 redirect_uri=redirect_uri,
                                 state=token.state,
                                 code=token.code)

    def test_invalid_response_request(self, mock_post):
        """This test ensures that a failed authorize request against the oauth
        endpoint succeeds with expected values.
        """
        self._mock_response(mock_post, valid=False)

        random_state = six.text_type(uuid.uuid4())

        # Simple GET with various parameters
        response = self.get_json(path='/openid/authorize_return',
                                 expect_errors=True,
                                 state=random_state,
                                 **self.valid_params)

        redirect_uri = self.valid_params['sb_redirect_uri']
        # Validate the redirect response
        self.assertValidRedirect(response=response,
                                 expected_status_code=302,
                                 redirect_uri=redirect_uri,
                                 error='access_denied',
                                 error_description=e_msg.OPEN_ID_TOKEN_INVALID)

    def test_invalid_redirect_no_name(self, mock_post):
        """If the oauth response to storyboard is valid, but does not include a
        first name, it should error.
        """
        self._mock_response(mock_post, valid=True)

        random_state = six.text_type(uuid.uuid4())

        invalid_params = self.valid_params.copy()
        del invalid_params['openid.sreg.fullname']

        # Simple GET with various parameters
        response = self.get_json(path='/openid/authorize_return',
                                 expect_errors=True,
                                 state=random_state,
                                 **invalid_params)

        redirect_uri = self.valid_params['sb_redirect_uri']
        # Validate the redirect response
        self.assertValidRedirect(response=response,
                                 expected_status_code=302,
                                 redirect_uri=redirect_uri,
                                 error='invalid_request',
                                 error_description=e_msg.INVALID_NO_NAME)

    def test_invalid_redirect_no_email(self, mock_post):
        """If the oauth response to storyboard is valid, but does not include a
        first name, it should error.
        """
        self._mock_response(mock_post, valid=True)

        random_state = six.text_type(uuid.uuid4())

        invalid_params = self.valid_params.copy()
        del invalid_params['openid.sreg.email']

        # Simple GET with various parameters
        response = self.get_json(path='/openid/authorize_return',
                                 expect_errors=True,
                                 state=random_state,
                                 **invalid_params)

        redirect_uri = self.valid_params['sb_redirect_uri']
        # Validate the redirect response
        self.assertValidRedirect(response=response,
                                 expected_status_code=302,
                                 redirect_uri=redirect_uri,
                                 error='invalid_request',
                                 error_description=e_msg.INVALID_NO_EMAIL)


class TestOAuthAccessToken(BaseOAuthTest):
    """Functional test for the /oauth/token endpoint for the generation of
    access tokens.
    """

    tested_timezones = [
        'Etc/GMT',
        'Etc/GMT+0',
        'Etc/GMT+1',
        'Etc/GMT+10',
        'Etc/GMT+11',
        'Etc/GMT+12',
        'Etc/GMT+2',
        'Etc/GMT+3',
        'Etc/GMT+4',
        'Etc/GMT+5',
        'Etc/GMT+6',
        'Etc/GMT+7',
        'Etc/GMT+8',
        'Etc/GMT+9',
        'Etc/GMT-0',
        'Etc/GMT-1',
        'Etc/GMT-10',
        'Etc/GMT-11',
        'Etc/GMT-12',
        'Etc/GMT-13',
        'Etc/GMT-14',
        'Etc/GMT-2',
        'Etc/GMT-3',
        'Etc/GMT-4',
        'Etc/GMT-5',
        'Etc/GMT-6',
        'Etc/GMT-7',
        'Etc/GMT-8',
        'Etc/GMT-9',
    ]

    def test_valid_access_request(self):
        """This test ensures that the access token request may execute
        properly with a valid token.
        """

        # Generate a valid auth token
        with base.HybridSessionManager():
            authorization_code = auth_api.authorization_code_save({
                'user_id': 2,
                'state': 'test_state',
                'code': 'test_valid_code'
            })

        content_type = 'application/x-www-form-urlencoded'
        # POST with content: application/x-www-form-urlencoded
        response = self.app.post('/v1/openid/token',
                                 params={
                                     'code': authorization_code.code,
                                     'grant_type': 'authorization_code'
                                 },
                                 content_type=content_type,
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
        with base.HybridSessionManager():
            access_token = \
                token_api.access_token_get_by_token(token['access_token'])
        self.assertIsNotNone(access_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEqual(2, access_token.user_id)
        self.assertEqual(token['id_token'], access_token.user_id)
        self.assertEqual(token['expires_in'], CONF.oauth.access_token_ttl)
        self.assertEqual(token['expires_in'], access_token.expires_in)
        self.assertEqual(token['access_token'], access_token.access_token)

        # Assert that the refresh token is in the database
        with base.HybridSessionManager():
            refresh_token = \
                refresh_tokens.refresh_token_get_by_token(
                    token['refresh_token'])

        self.assertIsNotNone(refresh_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEqual(2, refresh_token.user_id)
        self.assertEqual(CONF.oauth.refresh_token_ttl,
                         refresh_token.expires_in)
        self.assertEqual(token['refresh_token'], refresh_token.refresh_token)

        # Assert that the authorization code is no longer in the database.
        with base.HybridSessionManager():
            none_code = \
                auth_api.authorization_code_get(authorization_code.code)
        self.assertIsNone(none_code)

    def test_valid_access_token_time(self):
        """Assert that a newly created access token is valid if storyboard is
        installed in a multitude of timezones.
        """

        # Store the old TZ info, if it exists.
        old_tz = None
        if 'TZ' in os.environ:
            old_tz = os.environ['TZ']

        # Convert now into every possible timezone out there :)
        for name in self.tested_timezones:

            # Override the 'default timezone' for the current runtime.
            os.environ['TZ'] = name

            # Create a token.
            with base.HybridSessionManager():
                authorization_code = auth_api.authorization_code_save({
                    'user_id': 2,
                    'state': 'test_state',
                    'code': 'test_valid_code',
                    'expires_in': 300
                })

            content_type = 'application/x-www-form-urlencoded'
            response = self.app.post('/v1/openid/token',
                                     params={
                                         'code': authorization_code.code,
                                         'grant_type': 'authorization_code'
                                     },
                                     content_type=content_type,
                                     expect_errors=True)

            # Assert that this is a valid call.
            self.assertEqual(200, response.status_code)

            # Reset the timezone.
            if old_tz:
                os.environ['TZ'] = old_tz
            else:
                del os.environ['TZ']

    def test_expired_access_token_time(self):
        """This test ensures that an access token is seen as expired if
        storyboard is installed in multiple timezones.
        """

        expired = datetime.datetime.now(pytz.utc) - datetime.timedelta(
            minutes=6)

        # Store the old TZ info, if it exists.
        old_tz = None
        if 'TZ' in os.environ:
            old_tz = os.environ['TZ']

        # Convert now into every possible timezone out there :)
        for name in self.tested_timezones:

            # Override the 'default timezone' for the current runtime.
            os.environ['TZ'] = name

            # Create a token.
            with base.HybridSessionManager():
                authorization_code = auth_api.authorization_code_save({
                    'user_id': 2,
                    'state': 'test_state',
                    'code': 'test_valid_code',
                    'expires_in': 300,
                    'created_at': expired
                })

            content_type = 'application/x-www-form-urlencoded'
            # POST with content: application/x-www-form-urlencoded
            response = self.app.post('/v1/openid/token',
                                     params={
                                         'code': authorization_code.code,
                                         'grant_type': 'authorization_code'
                                     },
                                     content_type=content_type,
                                     expect_errors=True)

            # Assert that this is a valid call.
            self.assertEqual(401, response.status_code)

            # Reset the timezone.
            if old_tz:
                os.environ['TZ'] = old_tz
            else:
                del os.environ['TZ']

    def test_invalid_grant_type(self):
        """This test ensures that invalid grant_type parameters get the
        appropriate error response.
        """

        # Generate a valid auth token
        with base.HybridSessionManager():
            authorization_code = auth_api.authorization_code_save({
                'user_id': 2,
                'state': 'test_state',
                'code': 'test_valid_code',
                'expires_in': 300
            })

        content_type = 'application/x-www-form-urlencoded'
        # POST with content: application/x-www-form-urlencoded
        response = self.app.post('/v1/openid/token',
                                 params={
                                     'code': authorization_code.code,
                                     'grant_type': 'invalid_grant_type'
                                 },
                                 content_type=content_type,
                                 expect_errors=True)

        # Assert that this is a successful response
        self.assertEqual(400, response.status_code)
        self.assertIsNotNone(response.json)
        self.assertEqual('unsupported_grant_type', response.json['error'])
        self.assertEqual(e_msg.INVALID_TOKEN_GRANT_TYPE,
                         response.json['error_description'])

    def test_invalid_access_token(self):
        """This test ensures that invalid grant_type parameters get the
        appropriate error response.
        """

        content_type = 'application/x-www-form-urlencoded'
        # POST with content: application/x-www-form-urlencoded
        response = self.app.post('/v1/openid/token',
                                 params={
                                     'code': 'invalid_access_token',
                                     'grant_type': 'invalid_grant_type'
                                 },
                                 content_type=content_type,
                                 expect_errors=True)

        # Assert that this is a successful response
        self.assertEqual(400, response.status_code)
        self.assertIsNotNone(response.json)
        self.assertEqual('unsupported_grant_type', response.json['error'])
        self.assertEqual(e_msg.INVALID_TOKEN_GRANT_TYPE,
                         response.json['error_description'])

    def test_valid_refresh_token(self):
        """This test ensures that a valid refresh token can be converted into
        a valid access token, and cleans up after itself.
        """

        # Generate a valid access code
        with base.HybridSessionManager():
            authorization_code = auth_api.authorization_code_save({
                'user_id': 2,
                'state': 'test_state',
                'code': 'test_valid_code'
            })

        content_type = 'application/x-www-form-urlencoded'
        # Generate an auth and a refresh token.
        resp_1 = self.app.post('/v1/openid/token',
                               params={
                                   'code': authorization_code.code,
                                   'grant_type': 'authorization_code'
                               },
                               content_type=content_type,
                               expect_errors=True)

        # Assert that this is a successful response
        self.assertEqual(200, resp_1.status_code)

        # Assert that the token came back in the response
        t1 = resp_1.json

        # Assert that both are in the database.
        with base.HybridSessionManager():
            access_token = \
                token_api.access_token_get_by_token(t1['access_token'])
        self.assertIsNotNone(access_token)

        with base.HybridSessionManager():
            refresh_token = refresh_tokens.refresh_token_get_by_token(
                t1['refresh_token'])

        self.assertIsNotNone(refresh_token)

        content_type = 'application/x-www-form-urlencoded'
        # Issue a refresh token request.
        resp_2 = self.app.post('/v1/openid/token',
                               params={
                                   'refresh_token': t1['refresh_token'],
                                   'grant_type': 'refresh_token'
                               },
                               content_type=content_type,
                               expect_errors=True)

        # Assert that the response is good.
        self.assertEqual(200, resp_2.status_code)

        # Assert that the token came back in the response
        t2 = resp_2.json
        self.assertIsNotNone(t2['access_token'])
        self.assertIsNotNone(t2['expires_in'])
        self.assertIsNotNone(t2['id_token'])
        self.assertIsNotNone(t2['refresh_token'])
        self.assertIsNotNone(t2['token_type'])
        self.assertEqual('Bearer', t2['token_type'])

        # Assert that the access token is in the database
        with base.HybridSessionManager():
            new_access_token = \
                token_api.access_token_get_by_token(t2['access_token'])
        self.assertIsNotNone(new_access_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEqual(2, new_access_token.user_id)
        self.assertEqual(t2['id_token'], new_access_token.user_id)
        self.assertEqual(t2['expires_in'], CONF.oauth.access_token_ttl)
        self.assertEqual(t2['expires_in'], new_access_token.expires_in)
        self.assertEqual(t2['access_token'],
                         new_access_token.access_token)

        # Assert that the refresh token is in the database

        with base.HybridSessionManager():
            new_refresh_token = refresh_tokens.refresh_token_get_by_token(
                t2['refresh_token'])

        self.assertIsNotNone(new_refresh_token)

        # Assert that system configured values is owned by the correct user.
        self.assertEqual(2, new_refresh_token.user_id)
        self.assertEqual(CONF.oauth.refresh_token_ttl,
                         new_refresh_token.expires_in)
        self.assertEqual(t2['refresh_token'],
                         new_refresh_token.refresh_token)

        # Assert that the old access tokens are no longer in the database and
        # have been cleaned up.

        with base.HybridSessionManager():
            no_access_token = \
                token_api.access_token_get_by_token(t1['access_token'])
        with base.HybridSessionManager():
            no_refresh_token = \
                refresh_tokens.refresh_token_get_by_token(t1['refresh_token'])

        self.assertIsNone(no_refresh_token)
        self.assertIsNone(no_access_token)

    def test_invalid_refresh_token(self):
        """This test ensures that an invalid refresh token can be converted
        into a valid access token.
        """

        content_type = 'application/x-www-form-urlencoded'
        # Generate an auth and a refresh token.
        resp_1 = self.app.post('/v1/openid/token',
                               params={
                                   'refresh_token': 'invalid_refresh_token',
                                   'grant_type': 'refresh_token'
                               },
                               content_type=content_type,
                               expect_errors=True)

        # Assert that this is a correct response
        self.assertEqual(401, resp_1.status_code)
        self.assertIsNotNone(resp_1.json)
        self.assertEqual('invalid_grant', resp_1.json['error'])
