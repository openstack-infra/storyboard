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

from oslo.config import cfg
from pecan import expose
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
import six
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1.user_preferences import UserPreferencesController
from storyboard.api.v1.user_tokens import UserTokensController
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.db.api import users as users_api
from storyboard.openstack.common.gettextutils import _  # noqa


CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class UsersController(rest.RestController):
    """Manages users."""

    # Import the user preferences.
    preferences = UserPreferencesController()

    # Import user token management.
    tokens = UserTokensController()

    _custom_actions = {"search": ["GET"]}

    validation_post_schema = validations.USERS_POST_SCHEMA
    validation_put_schema = validations.USERS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], int, int, unicode, unicode, unicode,
                         unicode)
    def get(self, marker=None, limit=None, username=None, full_name=None,
            sort_field='id', sort_dir='asc'):
        """Page and filter the users in storyboard.

        :param marker: The resource id where the page should begin.
        :param limit The number of users to retrieve.
        :param username A string of characters to filter the username with.
        :param full_name A string of characters to filter the full_name with.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_user = users_api.user_get(marker)

        users = users_api.user_get_all(marker=marker_user, limit=limit,
                                       username=username, full_name=full_name,
                                       filter_non_public=True,
                                       sort_field=sort_field,
                                       sort_dir=sort_dir)
        user_count = users_api.user_get_count(username=username,
                                              full_name=full_name)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(user_count)
        if marker_user:
            response.headers['X-Marker'] = str(marker_user.id)

        return [wmodels.User.from_db_model(u) for u in users]

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.User, int)
    def get_one(self, user_id):
        """Retrieve details about one user.

        :param user_id: The unique id of this user
        """

        filter_non_public = True
        if user_id == request.current_user_id:
            filter_non_public = False

        user = users_api.user_get(user_id, filter_non_public)
        if not user:
            raise ClientSideError(_("User %s not found") % user_id,
                                  status_code=404)
        return user

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.User, body=wmodels.User)
    def post(self, user):
        """Create a new user.

        :param user: a user within the request body.
        """

        created_user = users_api.user_create(user.as_dict())
        return wmodels.User.from_db_model(created_user)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.User, int, body=wmodels.User)
    def put(self, user_id, user):
        """Modify this user.

        :param user_id: unique id to identify the user.
        :param user: a user within the request body.
        """
        current_user = users_api.user_get(request.current_user_id)

        # Only owners and superadmins are allowed to modify users.
        if request.current_user_id != user_id \
                and not current_user.is_superuser:
            response.status_code = 403
            response.body = _("You are not allowed to update this user.")
            return response

        # Strip out values that you're not allowed to change.
        user_dict = user.as_dict(omit_unset=True)

        if not current_user.is_superuser:
            # Only superuser may create superusers or modify login permissions.
            if 'enable_login' in six.iterkeys(user_dict):
                del user_dict['enable_login']

            if 'is_superuser' in six.iterkeys(user_dict):
                del user_dict['is_superuser']

        updated_user = users_api.user_update(user_id, user_dict)
        return wmodels.User.from_db_model(updated_user)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], unicode, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for users.

        :param q: The query string.
        :return: List of Users matching the query.
        """

        users = SEARCH_ENGINE.users_query(q=q, marker=marker, limit=limit)

        return [wmodels.User.from_db_model(u) for u in users]

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) == 1:
            # It's a request by a name or id
            something = args[0]

            if something == "search":
                # Request to a search endpoint
                return self.search, args
            else:
                return self.get_one, args

        return super(UsersController, self)._route(args, request)
