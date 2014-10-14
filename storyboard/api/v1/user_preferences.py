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

from pecan import abort
from pecan import request
from pecan import rest
from pecan.secure import secure
import wsme.types as types
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
import storyboard.db.api.users as user_api


class UserPreferencesController(rest.RestController):
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(types.DictType(unicode, unicode), int)
    def get_all(self, user_id):
        """Return all preferences for the current user.
        """
        if request.current_user_id != user_id:
            abort(403)
            return

        return user_api.user_get_preferences(user_id)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(types.DictType(unicode, unicode), int,
                         body=types.DictType(unicode, unicode))
    def post(self, user_id, body):
        """Allow a user to update their preferences.
        """
        if request.current_user_id != user_id:
            abort(403)

        return user_api.user_update_preferences(user_id, body)
