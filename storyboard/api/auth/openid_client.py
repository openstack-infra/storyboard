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

import logging
from oslo.config import cfg
import requests

from storyboard.api.auth import utils

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


OPENID_OPTS = [
    cfg.StrOpt('openid_url',
               default='https://login.launchpad.net/+openid',
               help='OpenId Authentication endpoint')
]

CONF.register_opts(OPENID_OPTS)


class OpenIdClient(object):

    def send_openid_redirect(self, request, response):
        redirect_location = CONF.openid_url
        response.status_code = 303

        return_params = {
            "scope": str(request.params.get("scope")),
            "state": str(request.params.get("state")),
            "client_id": str(request.params.get("client_id")),
            "response_type": str(request.params.get("response_type")),
            "sb_redirect_uri": str(request.params.get("redirect_uri"))
        }

        #TODO(krotscheck): URI base should be fully inferred from the request.
        # assuming that the API is hosted at /api isn't good.
        return_to_url = request.host_url + "/api/v1/openid/authorize_return?" \
            + utils.join_params(return_params, encode=True)

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
            "openid.sreg.required": "fullname,email,nickname",

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

    def verify_openid(self, request, response):
        verify_params = dict(request.params.copy())
        verify_params["openid.mode"] = "check_authentication"

        verify_response = requests.post(CONF.openid_url, data=verify_params)
        verify_data_tokens = verify_response.content.split()
        verify_dict = dict((token.split(":")[0], token.split(":")[1])
                           for token in verify_data_tokens)

        if (verify_response.status_code / 100 != 2
            or verify_dict['is_valid'] != 'true'):
            response.status_code = 401  # Unauthorized
            return False

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
