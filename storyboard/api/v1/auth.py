# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging

from oslo.config import cfg
import pecan
from pecan import request
from pecan import response
from pecan import rest

from storyboard.api.auth.oauth_validator import SERVER
from storyboard.api.auth.oauth_validator import TOKEN_STORAGE
from storyboard.api.auth.openid_client import client as openid_client

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

AUTH_OPTS = [
]
CONF.register_opts(AUTH_OPTS)


class AuthController(rest.RestController):
    _custom_actions = {
        "authorize": ["GET"],
        "authorize_return": ["GET"],
        "token": ["POST"],
    }

    @pecan.expose()
    def authorize(self):
        """Authorization code request."""

        return openid_client.send_openid_redirect(request, response)

    @pecan.expose()
    def authorize_return(self):
        """Authorization code redirect endpoint.
        At this point the server verifies an OpenId and retrieves user's
        e-mail and full name from request

        The client may already use both the e-mail and the fullname in the
        templates, even though there was no token request so far.

        """

        if not openid_client.verify_openid(request, response):
            # The verify call will set unauthorized code
            return response

        headers, body, code = SERVER.create_authorization_response(
            uri=request.url,
            http_method=request.method,
            body=request.body,
            scopes=request.params.get("scope"),
            headers=request.headers)

        response.headers = dict((str(k), str(v))
                                for k, v in headers.iteritems())
        response.status_code = code
        response.body = body or ''

        return response

    @pecan.expose()
    def token(self):
        """Access token endpoint."""

        auth_code = request.params.get("code")
        code_info = TOKEN_STORAGE.get_authorization_code_info(auth_code)

        headers, body, code = SERVER.create_token_response(
            uri=request.url,
            http_method=request.method,
            body=request.body,
            headers=request.headers)

        response.headers = dict((str(k), str(v))
                                for k, v in headers.iteritems())
        response.status_code = code

        json_body = json.loads(body)
        json_body.update({
            'id_token': code_info.user_id
        })

        response.body = json.dumps(json_body)
        return response
