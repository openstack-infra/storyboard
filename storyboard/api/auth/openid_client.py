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

from oslo_config import cfg
from oslo_log import log
import requests
import six
from six.moves.urllib.parse import urlparse

from storyboard.api.auth import ErrorMessages as e_msg
from storyboard.api.auth import utils
from storyboard.common.exception import AccessDenied
from storyboard.common.exception import InvalidClient
from storyboard.common.exception import InvalidRequest
from storyboard.common.exception import InvalidScope
from storyboard.common.exception import UnauthorizedClient
from storyboard.common.exception import UnsupportedResponseType


LOG = log.getLogger(__name__)
CONF = cfg.CONF


class OpenIdClient(object):
    def send_openid_redirect(self, request, response):

        # Extract needed parameters
        redirect_uri = request.params.get("redirect_uri")
        response_type = request.params.get("response_type")
        client_id = request.params.get("client_id")
        scope = request.params.get("scope")

        # Sanity Check: Redirect URI
        if not redirect_uri:
            raise InvalidRequest(message=e_msg.NO_REDIRECT_URI)

        parts = urlparse(redirect_uri)
        if not parts.scheme or not parts.path:
            raise InvalidRequest(message=e_msg.INVALID_REDIRECT_URI)

        # Sanity Check: response_type
        if not response_type:
            raise UnsupportedResponseType(redirect_uri=redirect_uri,
                                          message=e_msg.NO_RESPONSE_TYPE)
        if response_type != 'code':
            raise UnsupportedResponseType(redirect_uri=redirect_uri,
                                          message=e_msg.INVALID_RESPONSE_TYPE)

        # Sanity Check: client_id
        if not client_id:
            raise InvalidClient(redirect_uri=redirect_uri,
                                message=e_msg.NO_CLIENT_ID)
        if client_id not in CONF.oauth.valid_oauth_clients:
            raise UnauthorizedClient(redirect_uri=redirect_uri,
                                     message=e_msg.INVALID_CLIENT_ID)

        # Sanity Check: scope
        if not scope:
            raise InvalidScope(redirect_uri=redirect_uri,
                               message=e_msg.NO_SCOPE)
        # TODO(krotscheck): Defer scope check to ACL once available.
        if scope != 'user':
            raise InvalidScope(redirect_uri=redirect_uri,
                               message=e_msg.INVALID_SCOPE)

        redirect_location = CONF.oauth.openid_url
        response.status_code = 303

        return_params = {
            "scope": six.text_type(scope),
            "state": six.text_type(request.params.get("state")),
            "client_id": six.text_type(client_id),
            "response_type": six.text_type(response_type),
            "sb_redirect_uri": six.text_type(redirect_uri)
        }

        # TODO(krotscheck): URI base should be fully inferred from the request.
        # assuming that the API is hosted at /api isn't good.
        return_to_url = "%s/api/v1/openid/authorize_return?%s" % (
            request.host_url,
            utils.join_params(return_params, encode=True)
        )

        response.status_code = 303

        openid_params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",

            "openid.claimed_id": "http://specs.openid.net/auth/2.0/"
                                 "identifier_select",
            "openid.identity": "http://specs.openid.net/auth/2.0/"
                               "identifier_select",

            "openid.realm": request.host_url,
            "openid.return_to": return_to_url,

            "openid.ns.sreg": "http://openid.net/sreg/1.0",
            "openid.sreg.required": "fullname,email",

            "openid.ns.ext2": "http://openid.net/srv/ax/1.0",
            "openid.ext2.mode": "fetch_request",
            "openid.ext2.type.FirstName": "http://schema.openid.net/"
                                          "namePerson/first",
            "openid.ext2.type.LastName": "http://schema.openid.net/"
                                         "namePerson/last",
            "openid.ext2.type.Email": "http://schema.openid.net/contact/email",
            "openid.ext2.required": "FirstName,LastName,Email"
        }
        joined_params = utils.join_params(openid_params)

        redirect_location = redirect_location + '?' + joined_params
        response.headers["Location"] = redirect_location

        return response

    def verify_openid(self, request):
        verify_params = dict(request.params.copy())
        verify_params["openid.mode"] = "check_authentication"
        redirect_uri = request.params['sb_redirect_uri'] or None

        verify_response = requests.post(CONF.oauth.openid_url,
                                        data=verify_params)
        content = verify_response.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        verify_data_tokens = content.split()

        verify_dict = dict((token.split(":")[0], token.split(":")[1])
                           for token in verify_data_tokens)

        if (verify_response.status_code / 100 != 2
                or verify_dict['is_valid'] != 'true'):
            raise AccessDenied(redirect_uri=redirect_uri,
                               message=e_msg.OPEN_ID_TOKEN_INVALID)

        # Is the data we've received within our required parameters?
        required_parameters = {
            'openid.sreg.email': e_msg.INVALID_NO_EMAIL,
            'openid.sreg.fullname': e_msg.INVALID_NO_NAME,
        }

        for name, error in six.iteritems(required_parameters):
            if name not in verify_params or not verify_params[name]:
                raise InvalidRequest(redirect_uri=redirect_uri,
                                     message=error)

        return True

    def create_association(self, op_location):
        # Let's skip it for MVP at least
        query_dict = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "associate",
            "openid.assoc_type": "HMAC-SHA256",
            "openid.session_type": "no-encryption"
        }
        assoc_data = requests.post(op_location, data=query_dict).content

        data_tokens = assoc_data.split()
        data_dict = dict((token.split(":")[0], token.split(":")[1])
                         for token in data_tokens)

        return data_dict["assoc_handle"]


client = OpenIdClient()
