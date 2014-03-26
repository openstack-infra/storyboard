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

from datetime import datetime

from oslo.config import cfg
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.db.api import users as users_api

CONF = cfg.CONF


class User(base.APIBase):
    """Represents a user."""

    username = wtypes.text
    """A short unique name, beginning with a lower-case letter or number, and
    containing only letters, numbers, dots, hyphens, or plus signs"""

    full_name = wtypes.text
    """Full (Display) name."""

    openid = wtypes.text
    """The unique identifier, returned by an OpneId provider"""

    email = wtypes.text
    """Email Address."""

    # Todo(nkonovalov): use teams to define superusers
    is_superuser = bool

    last_login = datetime
    """Date of the last login."""

    @classmethod
    def sample(cls):
        return cls(
            username="elbarto",
            full_name="Bart Simpson",
            openid="https://login.launchpad.net/+id/Abacaba",
            email="skinnerstinks@springfield.net",
            is_staff=False,
            is_active=True,
            is_superuser=True,
            last_login=datetime(2014, 1, 1, 16, 42))


class UsersController(rest.RestController):
    """Manages users."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose([User], int, int)
    def get(self, marker=None, limit=None):
        """Retrieve definitions of all of the users.

        :param marker The marker at which the page set should begin. At the
        moment, this is the unique resource id..
        :param limit The number of users to retrieve.
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_user = users_api.user_get(marker)

        users = users_api.user_get_all(marker=marker_user, limit=limit)
        user_count = users_api.user_get_count()

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(user_count)
        if marker_user:
            response.headers['X-Marker'] = str(marker_user.id)

        return [User.from_db_model(u) for u in users]

    @secure(checks.guest)
    @wsme_pecan.wsexpose(User, int)
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
    @wsme_pecan.wsexpose(User, body=User)
    def post(self, user):
        """Create a new user.

        :param user: a user within the request body.
        """

        created_user = users_api.user_create(user.as_dict())
        return User.from_db_model(created_user)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(User, int, body=User)
    def put(self, user_id, user):
        """Modify this user.

        :param user_id: unique id to identify the user.
        :param user: a user within the request body.
        """

        if request.current_user_id != user_id:
            response.status_code = 400
            response.body = "You are not allowed to update another user."

        user_dict = user.as_dict()
        if "openid" in user_dict or "is_superuser" in user_dict:
            response.status_code = 400
            response.body = "You are not allowed to update " \
                            "your identity fields."
            return response

        updated_user = users_api.user_update(user_id, user_dict)
        return User.from_db_model(updated_user)
