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

import datetime
import pytz

from oauthlib.oauth2 import RequestValidator
from oauthlib.oauth2 import WebApplicationServer
from oslo.config import cfg
from oslo_log import log

from storyboard.db.api import access_tokens as token_api
from storyboard.db.api import auth_codes as auth_api
from storyboard.db.api import refresh_tokens as refresh_token_api
from storyboard.db.api import users as user_api

CONF = cfg.CONF
LOG = log.getLogger(__name__)


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

        # todo(nkonovalov): check an uri based on CONF.domain
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
        last_login = datetime.datetime.now(pytz.utc)

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

        # def save_authorization_code(self, authorization_code, user_id):
        values = {
            "code": code["code"],
            "state": code["state"],
            "user_id": user.id,
            "expires_in": CONF.oauth.authorization_code_ttl
        }
        auth_api.authorization_code_save(values)

    # Token request

    def authenticate_client(self, request, *args, **kwargs):
        """Skip the authentication here. It is handled through an OpenId client
        The parameters are set to match th OAuth protocol.

        """

        setattr(request, "client", type("Object", (object,), {})())
        setattr(request.client, "client_id", "1")
        return True

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """Validate the code belongs to the client. It must exist, and it
        must be recent.
        """

        db_code = auth_api.authorization_code_get(code)
        if not db_code:
            return False

        # Calculate the expiration date.
        expires_on = db_code.created_at + datetime.timedelta(
            seconds=db_code.expires_in)

        # Generate a UTC now() with timezone attached so we can run a
        # comparison against the timezone-sensitive result that comes from
        # the database.
        now = datetime.datetime.now(tz=pytz.utc)

        return expires_on > now

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client,
                             *args, **kwargs):
        """Check that the client is allowed to redirect using the given
        redirect_uri.

        """

        # todo(nkonovalov): check an uri based on CONF.domain
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
            code_info = auth_api.authorization_code_get(code)
            return code_info.user_id

        # Try refresh token
        refresh_token = request._params.get("refresh_token")
        refresh_token_entry = \
            refresh_token_api.refresh_token_get_by_token(refresh_token)
        if refresh_token_entry:
            return refresh_token_entry.user_id

        return None

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Save all token information to the storage."""

        user_id = self._resolve_user_id(request)

        # If a refresh_token was used to obtain a new access_token, it (and
        # its access token) should be removed.
        self.invalidate_refresh_token(request)

        access_token_values = {
            "access_token": token["access_token"],
            "expires_in": token["expires_in"],
            "expires_at": datetime.datetime.now(pytz.utc) + datetime.timedelta(
                seconds=token["expires_in"]),
            "user_id": user_id
        }
        access_token = token_api.access_token_create(access_token_values)

        # Oauthlib does not provide a separate expiration time for a
        # refresh_token so taking it from config directly.
        refresh_expires_in = CONF.oauth.refresh_token_ttl

        refresh_token_values = {
            "refresh_token": token["refresh_token"],
            "user_id": user_id,
            "expires_in": refresh_expires_in,
            "expires_at": datetime.datetime.now(pytz.utc) + datetime.timedelta(
                seconds=refresh_expires_in),
        }
        refresh_token_api.refresh_token_create(access_token.id,
                                               refresh_token_values)

    def invalidate_authorization_code(self, client_id, code, request, *args,
                                      **kwargs):
        """Authorization codes are use once, invalidate it when a token has
        been acquired.

        """

        auth_api.authorization_code_delete(code)

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
        return refresh_token_api.is_valid(refresh_token)

    def invalidate_refresh_token(self, request):
        """Remove a used token from the storage."""

        refresh_token = request._params.get("refresh_token")

        # The request may have no token in parameters which means that the
        # authorization code was used.
        if not refresh_token:
            return

        r_token = refresh_token_api.refresh_token_get_by_token(refresh_token)
        token_api.access_token_delete(
            refresh_token_api.get_access_token_id(r_token.id)
        )  # Cascades


class OpenIdConnectServer(WebApplicationServer):

    def __init__(self, request_validator):
        access_token_ttl = CONF.oauth.access_token_ttl
        super(OpenIdConnectServer, self).__init__(
            request_validator,
            token_expires_in=access_token_ttl)

validator = SkeletonValidator()
SERVER = OpenIdConnectServer(validator)
