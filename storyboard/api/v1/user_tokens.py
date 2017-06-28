# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import uuid

from oslo_config import cfg
from oslo_log import log
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
import six
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
import storyboard.api.v1.wmodels as wmodels
from storyboard.common import decorators
import storyboard.db.api.user_tokens as token_api
import storyboard.db.api.users as user_api


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class UserTokensController(rest.RestController):
    _custom_actions = {"delete_all": ["DELETE"]}

    def _from_db_model(self, access_token):
        access_token_model = wmodels.AccessToken.from_db_model(
            access_token,
            skip_fields="refresh_token")

        if access_token.refresh_token:
            access_token_model.refresh_token = wmodels.RefreshToken \
                .from_db_model(access_token.refresh_token)

        return access_token_model

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose([wmodels.AccessToken], int, int, int, wtypes.text,
                         wtypes.text)
    def get_all(self, user_id, marker=None, limit=None, sort_field='id',
                sort_dir='asc'):
        """Returns all the access tokens with matching refresh tokens for
        the provided user.

        Example::

          curl https://my.example.org/api/v1/users/21/tokens \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param user_id: The ID of the user.
        :param marker: The marker record at which to start the page.
        :param limit: The number of records to return.
        :param sort_field: The field on which to sort.
        :param sort_dir: The direction to sort.
        :return: A list of access tokens for the given user.
        """
        self._assert_can_access(user_id)

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_token = token_api.user_token_get(marker)

        tokens = token_api.user_token_get_all(marker=marker_token,
                                              limit=limit,
                                              user_id=user_id,
                                              filter_non_public=True,
                                              sort_field=sort_field,
                                              sort_dir=sort_dir)
        token_count = token_api.user_token_get_count(user_id=user_id)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(token_count)

        if marker_token:
            response.headers['X-Marker'] = str(marker_token.id)

        return [self._from_db_model(t) for t in tokens]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.AccessToken, int, int)
    def get(self, user_id, access_token_id):
        """Returns a specific access token with assigned refresh token for the
        given user. Admin users can specify any user id, regular users can only
        use their own.

        Example::

          curl https://my.example.org/api/v1/users/2/tokens \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param user_id: The ID of the user.
        :param access_token_id: The ID of the access token.
        :return: The requested access token.
        """
        access_token = token_api.user_token_get(access_token_id)
        self._assert_can_access(user_id, access_token)

        if not access_token:
            abort(404, _("Token %s not found.") % access_token_id)

        return self._from_db_model(access_token)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.AccessToken, int, body=wmodels.AccessToken)
    def post(self, user_id, body):
        """Create a new access token with assigned refresh token for the given
        user. Admin users can specify any user id, regular users can only use
        their own.

        Example::

          curl https://my.example.org/api/v1/users/2/tokens \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"expires_in": 3600, "user_id": 2}'

        :param user_id: The user ID of the user.
        :param body: The access token.
        :return: The created access token.
        """
        self._assert_can_access(user_id, body)

        # Generate a random token if one was not provided.
        if not body.access_token:
            body.access_token = six.text_type(uuid.uuid4())

        # Token duplication check.
        dupes = token_api.user_token_get_all(
            access_token=body.access_token
        )

        if dupes:
            abort(409, _('This token already exist.'))

        token_dict = body.as_dict()

        if "refresh_token" in token_dict:
            del token_dict["refresh_token"]

        token = token_api.user_token_create(token_dict)

        if not token:
            abort(400, _("Can't create access token."))

        return self._from_db_model(token)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.AccessToken, int, int,
                         body=wmodels.AccessToken)
    def put(self, user_id, access_token_id, body):
        """Update an access token for the given user. Admin users can edit
        any token, regular users can only edit their own.

        Example::

          curl https://my.example.org/api/v1/users/2/tokens/1764 \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"expires_in": 7200, "user_id": 2}'

        :param user_id: The user ID of the user.
        :param access_token_id: The ID of the access token.
        :param body: The access token.
        :return: The created access token.
        """

        target_token = token_api.user_token_get(access_token_id)

        self._assert_can_access(user_id, body)
        self._assert_can_access(user_id, target_token)

        if not target_token:
            abort(404, _("Token %s not found.") % access_token_id)

        # We only allow updating the expiration date.
        target_token.expires_in = body.expires_in

        token_dict = target_token.as_dict()

        if "refresh_token" in token_dict:
            del token_dict["refresh_token"]

        result_token = token_api.user_token_update(access_token_id,
                                                   token_dict)

        return self._from_db_model(result_token)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int, status_code=204)
    def delete(self, user_id, access_token_id):
        """Deletes an access token with assigned refresh token for the given
        user. Admin users can delete any access tokens, regular users can only
        delete their own.

        Example::

          curl https://my.example.org/api/v1/users/2/tokens/1764 -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param user_id: The user ID of the user.
        :param access_token_id: The ID of the access token.
        :return: Empty body, or error response.
        """
        access_token = token_api.user_token_get(access_token_id)
        self._assert_can_access(user_id, access_token)

        if not access_token:
            abort(404, _("Token %s not found.") % access_token_id)

        token_api.user_token_delete(access_token_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.AccessToken, int, status_code=204)
    def delete_all(self, user_id):
        """Deletes all access tokens for the given user.

        Example::

          curl https://my.example.com/v1/users/2/tokens/delete_all -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param user_id: The user ID of the user.
        """

        token_api.delete_all_user_tokens(user_id)

    def _assert_can_access(self, user_id, token_entity=None):
        current_user = user_api.user_get(request.current_user_id)

        if not user_id:
            abort(400, _("user_id is missing."))

        # The user must be logged in.
        if not current_user:
            abort(401, _("You must log in to do this."))

        # If the impacted user is not the current user, the current user must
        # be an admin.
        if not current_user.is_superuser and current_user.id != user_id:
            abort(403, _("You are not admin and can't do this."))

        # The path-based impacted user and the user found in the entity must
        # be identical. No PUT /users/1/tokens { user_id: 2 }
        if token_entity and token_entity.user_id != user_id:
            abort(403, _("token_entity.user_id or user_id is wrong."))
