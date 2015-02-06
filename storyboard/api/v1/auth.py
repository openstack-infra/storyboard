# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from oslo_log import log
import pecan
from pecan import request
from pecan import response
from pecan import rest
import six

from storyboard.api.auth import ErrorMessages as e_msg
from storyboard.api.auth.oauth_validator import SERVER
from storyboard.api.auth.openid_client import client as openid_client
from storyboard.common import decorators
from storyboard.common.exception import UnsupportedGrantType
from storyboard.db.api import auth_codes as auth_api
from storyboard.db.api import refresh_tokens as refresh_token_api

LOG = log.getLogger(__name__)


class AuthController(rest.RestController):

    _custom_actions = {
        "authorize": ["GET"],
        "authorize_return": ["GET"],
        "token": ["POST"],
    }

    @decorators.oauth_exceptions
    @pecan.expose()
    def authorize(self):
        """Authorization code request."""

        return openid_client.send_openid_redirect(request, response)

    @decorators.oauth_exceptions
    @pecan.expose()
    def authorize_return(self):
        """Authorization code redirect endpoint.
        At this point the server verifies an OpenId and retrieves user's
        e-mail and full name from request

        The client may already use both the e-mail and the fullname in the
        templates, even though there was no token request so far.

        """

        # This will raise an exception if it's not valid
        openid_client.verify_openid(request)

        headers, body, code = SERVER.create_authorization_response(
            uri=request.url,
            http_method=request.method,
            body=request.body,
            scopes=request.params.get("scope"),
            headers=request.headers)

        response.headers = dict((str(k), str(v))
                                for k, v in six.iteritems(headers))
        response.status_code = code
        body = body or ''
        response.body = body.encode('utf-8')

        return response

    def _access_token_by_code(self):
        auth_code = request.params.get("code")
        code_info = auth_api.authorization_code_get(auth_code)
        headers, body, code = SERVER.create_token_response(
            uri=request.url,
            http_method=request.method,
            body=request.body,
            headers=request.headers)
        response.headers = dict((str(k), str(v))
                                for k, v in six.iteritems(headers))
        response.status_code = code
        json_body = json.loads(body)

        # Update a body with user_id only if a response is 2xx
        if code / 100 == 2:
            json_body.update({
                'id_token': code_info.user_id
            })

        response.json = json_body
        return response

    def _access_token_by_refresh_token(self):
        refresh_token = request.params.get("refresh_token")
        refresh_token_info = \
            refresh_token_api.refresh_token_get_by_token(refresh_token)

        headers, body, code = SERVER.create_token_response(
            uri=request.url,
            http_method=request.method,
            body=request.body,
            headers=request.headers)
        response.headers = dict((str(k), str(v))
                                for k, v in six.iteritems(headers))
        response.status_code = code
        json_body = json.loads(body)

        # Update a body with user_id only if a response is 2xx
        if code / 100 == 2:
            json_body.update({
                'id_token': refresh_token_info.user_id
            })

        response.json = json_body

        return response

    @decorators.oauth_exceptions
    @pecan.expose()
    def token(self):
        """Token endpoint."""

        grant_type = request.params.get("grant_type")

        if grant_type not in ["authorization_code", "refresh_token"]:
            raise UnsupportedGrantType(message=e_msg.INVALID_TOKEN_GRANT_TYPE)

        if grant_type == "authorization_code":
            # Serve an access token having an authorization code
            return self._access_token_by_code()

        if grant_type == "refresh_token":
            # Serve an access token having a refresh token
            return self._access_token_by_refresh_token()
