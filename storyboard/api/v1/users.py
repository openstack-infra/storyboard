# Copyright (c) 2013 Mirantis Inc.
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
from pecan import abort
from pecan import expose
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
import six
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1.user_preferences import UserPreferencesController
from storyboard.api.v1.user_tokens import UserTokensController
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import users as users_api


CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class UsersController(rest.RestController):
    """Manages users."""

    # Import the user preferences.
    preferences = UserPreferencesController()

    # Import user token management.
    tokens = UserTokensController()

    _custom_actions = {"search": ["GET"],
                       "self": ["GET"]}

    validation_post_schema = validations.USERS_POST_SCHEMA
    validation_put_schema = validations.USERS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], int, int, int, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text, wtypes.text,
                         wtypes.text)
    def get(self, marker=None, offset=None, limit=None, full_name=None,
            email=None, openid=None, sort_field='id', sort_dir='asc'):
        """Page and filter the users in storyboard.

        Example::

          curl https://my.example.org/api/v1/users

        :param marker: The resource id where the page should begin.
        :param offset: The offset to start the page at.
        :param limit: The number of users to retrieve.
        :param full_name: A string of characters to filter the full_name with.
        :param email: A string of characters to filter the email with.
        :param openid: A string of characters to filter the openid with.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_user = None
        if marker is not None:
            marker_user = users_api.user_get(marker)

        users = users_api.user_get_all(marker=marker_user,
                                       offset=offset,
                                       limit=limit,
                                       full_name=full_name,
                                       email=email,
                                       openid=openid,
                                       filter_non_public=True,
                                       sort_field=sort_field,
                                       sort_dir=sort_dir)
        user_count = users_api.user_get_count(full_name=full_name,
                                              email=email,
                                              openid=openid)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(user_count)
        if marker_user:
            response.headers['X-Marker'] = str(marker_user.id)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

        return [wmodels.User.from_db_model(u) for u in users]

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.User, int)
    def get_one(self, user_id):
        """Retrieve details about one user.

        Example::

          curl https://my.example.org/api/v1/users/21

        :param user_id: The unique id of this user
        """

        filter_non_public = True
        if user_id == request.current_user_id:
            filter_non_public = False

        user = users_api.user_get(user_id, filter_non_public)
        if not user:
            raise exc.NotFound(_("User %s not found") % user_id)
        return user

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.User, body=wmodels.User)
    def post(self, user):
        """Create a new user.
           This command is only available to Admin users.

        Example::

          TODO

        :param user: A user within the request body.
        """

        created_user = users_api.user_create(user.as_dict())
        return wmodels.User.from_db_model(created_user)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.User, int, body=wmodels.User)
    def put(self, user_id, user):
        """Modify this user. Admin users can edit the user details of any user,
        authenticated users can only modify their own details.

        Example::

          curl https://my.example.org/api/v1/users/21 -X PUT \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"email":"user@my.example.org"}'

        :param user_id: Unique id to identify the user.
        :param user: A user within the request body.
        """
        current_user = users_api.user_get(request.current_user_id)

        # Only owners and superadmins are allowed to modify users.
        if request.current_user_id != user_id \
                and not current_user.is_superuser:
            abort(403, _("You are not allowed to update this user."))

        # Strip out values that you're not allowed to change.
        user_dict = user.as_dict(omit_unset=True)

        if not current_user.is_superuser:
            # Only superuser may create superusers or modify login permissions.
            if 'enable_login' in six.iterkeys(user_dict):
                del user_dict['enable_login']

            if 'is_superuser' in six.iterkeys(user_dict):
                del user_dict['is_superuser']

        filter_non_public = True
        if user_id == request.current_user_id:
            filter_non_public = False

        updated_user = users_api.user_update(
            user_id, user_dict, filter_non_public)
        return wmodels.User.from_db_model(updated_user)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], wtypes.text, int, int, int)
    def search(self, q="", marker=None, offset=None, limit=None):
        """The search endpoint for users.

        Example::

          curl https://my.example.org/api/v1/users/search?q=James

        :param q: The query string.
        :return: List of Users matching the query.
        """

        users = SEARCH_ENGINE.users_query(q=q, marker=marker,
                                          offset=offset,
                                          limit=limit,
                                          filter_non_public=True)

        return [wmodels.User.from_db_model(u) for u in users]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.User)
    def self(self):
        """Return the currently logged in user

        Example::

          curl https://my.example.org/api/v1/users/self \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :return: The User record for the current user.
        """
        user = users_api.user_get(request.current_user_id,
                                  filter_non_public=False)

        if not user:
            raise exc.NotFound(_("User %s not found") %
                               request.current_user_id)
        return user

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) == 1:
            # It's a request by a name or id
            something = args[0]

            if something == "search":
                # Request to a search endpoint
                return self.search, args
            elif something == "self":
                # Return the currently logged in user
                return self.self, []
            else:
                return self.get_one, args

        return super(UsersController, self)._route(args, request)
