# Copyright (c) 2013 Mirantis Inc.
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

from oslo.config import cfg
from pecan import expose
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import wmodels
from storyboard.db.api import users as users_api

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class UsersController(rest.RestController):
    """Manages users."""

    _custom_actions = {"search": ["GET"]}

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
            raise ClientSideError("User %s not found" % user_id,
                                  status_code=404)
        return user

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.User, body=wmodels.User)
    def post(self, user):
        """Create a new user.

        :param user: a user within the request body.
        """

        created_user = users_api.user_create(user.as_dict())
        return wmodels.User.from_db_model(created_user)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.User, int, body=wmodels.User)
    def put(self, user_id, user):
        """Modify this user.

        :param user_id: unique id to identify the user.
        :param user: a user within the request body.
        """
        current_user = users_api.user_get(request.current_user_id)

        if not user or not user.id or not current_user:
            response.status_code = 404
            response.body = "Not found"
            return response

        # Only owners and superadmins are allowed to modify users.
        if request.current_user_id != user.id \
                and not current_user.is_superuser:
            response.status_code = 403
            response.body = "You are not allowed to update this user."
            return response

        # Strip out values that you're not allowed to change.
        user_dict = user.as_dict()

        # You cannot modify the openid field.
        del user_dict['openid']

        if not current_user.is_superuser:
            # Only superuser may create superusers or modify login permissions.
            del user_dict['enable_login']
            del user_dict['is_superuser']

        updated_user = users_api.user_update(user_id, user_dict)
        return wmodels.User.from_db_model(updated_user)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], unicode, unicode, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for users.

        :param q: The query string.
        :return: List of Users matching the query.
        """

        users = SEARCH_ENGINE.users_query(q=q, marker=marker, limit=limit)

        return [wmodels.User.from_db_model(u) for u in users]

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) > 0:
            # It's a request by a name or id
            something = args[0]

            if something == "search":
                # Request to a search endpoint
                return self.search, args
            else:
                return self.get_one, args

        return super(UsersController, self)._route(args, request)
