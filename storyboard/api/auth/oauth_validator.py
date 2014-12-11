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

from datetime import datetime

from oauthlib.oauth2 import RequestValidator
from oauthlib.oauth2 import WebApplicationServer
from oslo.config import cfg

from storyboard.api.auth.token_storage import storage
from storyboard.db.api import users as user_api
from storyboard.openstack.common import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)

TOKEN_OPTS = [
    cfg.IntOpt("access_token_ttl",
               default=60 * 60,  # One hour
               help="Time in seconds before an access_token expires"),

    cfg.IntOpt("refresh_token_ttl",
               default=60 * 60 * 24 * 7,  # One week
               help="Time in seconds before an refresh_token expires")
]

CONF.register_opts(TOKEN_OPTS)


class SkeletonValidator(RequestValidator):
    """This is oauth skeleton for handling all kind of validations and storage
    manipulations.

    As it is and OAuth2, not OpenId-connect, some methods are not required to
    be implemented.

    Scope parameter validation is skipped as it is not a part of OpenId-connect
    protocol.

    """

    def __init__(self):
        super(SkeletonValidator, self).__init__()
        self.token_storage = storage.get_storage()

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Check that a valid client is connecting

        """

        # Let's think about valid clients later
        return True

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args,
                              **kwargs):
        """Check that the client is allowed to redirect using the given
        redirect_uri.

        """

        #todo(nkonovalov): check an uri based on CONF.domain
        return True

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return request.sb_redirect_uri

    def validate_scopes(self, client_id, scopes, client, request, *args,
                        **kwargs):
        """Scopes are not supported in OpenId-connect
        The "user" value is hardcoded here to fill the difference between
        the protocols.

        """

        # Verify that the claimed user is allowed to log in.
        openid = request._params["openid.claimed_id"]
        user = user_api.user_get_by_openid(openid)

        if user and not user.enable_login:
            return False

        return scopes == "user"

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """Scopes a client will authorize for if none are supplied in the
        authorization request.

        """

        return ["user"]

    def validate_response_type(self, client_id, response_type, client, request,
                               *args, **kwargs):
        """Clients should only be allowed to use one type of response type, the
        one associated with their one allowed grant type.
        In this case it must be "code".

        """

        return response_type == "code"

    # Post-authorization

    def save_authorization_code(self, client_id, code, request, *args,
                                **kwargs):
        """Save the code to the storage and remove the state as it is persisted
        in the "code" argument
        """

        openid = request._params["openid.claimed_id"]
        email = request._params["openid.sreg.email"]
        full_name = request._params["openid.sreg.fullname"]
        username = request._params["openid.sreg.nickname"]
        last_login = datetime.utcnow()

        user = user_api.user_get_by_openid(openid)
        user_dict = {"full_name": full_name,
                     "username": username,
                     "email": email,
                     "last_login": last_login}

        if not user:
            user_dict.update({"openid": openid})
            user = user_api.user_create(user_dict)
        else:
            user = user_api.user_update(user.id, user_dict)

        self.token_storage.save_authorization_code(code, user_id=user.id)

    # Token request

    def authenticate_client(self, request, *args, **kwargs):
        """Skip the authentication here. It is handled through an OpenId client
        The parameters are set to match th OAuth protocol.

        """

        setattr(request, "client", type("Object", (object,), {})())
        setattr(request.client, "client_id", "1")
        return True

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """Validate the code belongs to the client."""

        return self.token_storage.check_authorization_code(code)

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client,
                             *args, **kwargs):
        """Check that the client is allowed to redirect using the given
        redirect_uri.

        """

        #todo(nkonovalov): check an uri based on CONF.domain
        return True

    def validate_grant_type(self, client_id, grant_type, client, request,
                            *args, **kwargs):
        """Clients should only be allowed to use one type of grant.
        In this case, it must be "authorization_code" or "refresh_token"

        """

        return (grant_type == "authorization_code"
                or grant_type == "refresh_token")

    def _resolve_user_id(self, request):

        # Try authorization code
        code = request._params.get("code")
        if code:
            code_info = self.token_storage.get_authorization_code_info(code)
            return code_info.user_id

        # Try refresh token
        refresh_token = request._params.get("refresh_token")
        refresh_token_entry = self.token_storage.get_refresh_token_info(
            refresh_token)
        if refresh_token_entry:
            return refresh_token_entry.user_id

        return None

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Save all token information to the storage."""

        user_id = self._resolve_user_id(request)

        # If a refresh_token was used to obtain a new access_token, it should
        # be removed.
        self.invalidate_refresh_token(request)

        self.token_storage.save_token(access_token=token["access_token"],
                                      expires_in=token["expires_in"],
                                      refresh_token=token["refresh_token"],
                                      user_id=user_id)

    def invalidate_authorization_code(self, client_id, code, request, *args,
                                      **kwargs):
        """Authorization codes are use once, invalidate it when a token has
        been acquired.

        """

        self.token_storage.invalidate_authorization_code(code)

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        """The check will be performed in a separate middleware."""

        pass

    # Token refresh request

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """Scopes a client will authorize for if none are supplied in the
        authorization request.

        """
        return ["user"]

    def rotate_refresh_token(self, request):
        """The refresh token should be single use."""

        return True

    def validate_refresh_token(self, refresh_token, client, request, *args,
                               **kwargs):
        """Check that the refresh token exists in the db."""

        return self.token_storage.check_refresh_token(refresh_token)

    def invalidate_refresh_token(self, request):
        """Remove a used token from the storage."""

        refresh_token = request._params.get("refresh_token")

        # The request may have no token in parameters which means that the
        # authorization code was used.
        if not refresh_token:
            return

        self.token_storage.invalidate_refresh_token(refresh_token)


class OpenIdConnectServer(WebApplicationServer):

    def __init__(self, request_validator):
        access_token_ttl = CONF.access_token_ttl
        super(OpenIdConnectServer, self).__init__(
            request_validator,
            token_expires_in=access_token_ttl)

validator = SkeletonValidator()
SERVER = OpenIdConnectServer(validator)
