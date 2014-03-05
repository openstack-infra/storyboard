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

from pecan import rest
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

import storyboard.api.v1.wsme_models as wsme_models


class UsersController(rest.RestController):
    """Manages users."""

    @wsme_pecan.wsexpose([wsme_models.User])
    def get(self):
        """Retrieve definitions of all of the users."""
        users = wsme_models.User.get_all()
        return users

    @wsme_pecan.wsexpose(wsme_models.User, int)
    def get_one(self, user_id):
        """Retrieve details about one user.

        :param user_id: The unique id of this user
        """
        user = wsme_models.User.get(id=user_id)
        if not user:
            raise ClientSideError("User %s not found" % user_id,
                                  status_code=404)
        return user

    @wsme_pecan.wsexpose(wsme_models.User, wsme_models.User)
    def post(self, user):
        """Create a new user.

        :param user: a user within the request body.
        """
        created_user = wsme_models.User.create(wsme_entry=user)
        if not created_user:
            raise ClientSideError("Could not create User")
        return created_user

    @wsme_pecan.wsexpose(wsme_models.User, int, wsme_models.User)
    def put(self, user_id, user):
        """Modify this user.

        :param user_id: unique id to identify the user.
        :param user: a user within the request body.
        """
        updated_user = wsme_models.User.update("id", user_id, user)
        if not updated_user:
            raise ClientSideError("Could not update user %s" % user_id)
        return updated_user
