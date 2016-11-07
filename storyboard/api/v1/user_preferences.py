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

from oslo_config import cfg
from oslo_log import log
from pecan import abort
from pecan import request
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import validations
from storyboard.common import decorators
import storyboard.db.api.users as user_api


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class UserPreferencesController(rest.RestController):
    validation_post_schema = validations.USER_PREFERENCES_POST_SCHEMA

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.DictType(wtypes.text, wtypes.text), int)
    def get_all(self, user_id):
        """Return all preferences for the current user.

        Example::

          curl https://my.example.org/api/v1/users/21/preferences \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param user_id: An ID of the user.
        """

        if request.current_user_id != user_id:
            abort(403, _("You can't read preferences of other users."))
            return

        return user_api.user_get_preferences(user_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wtypes.DictType(wtypes.text, wtypes.text), int,
                         body=wtypes.DictType(wtypes.text, wtypes.text))
    def post(self, user_id, body):
        """Allow a user to update their preferences. Note that a user must
        explicitly set a preference value to Null/None to have it deleted.

        Example::

          curl https://my.example.org/api/v1/users/21/preferences \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"display_events_tags_added":"false"}'

        :param user_id: The ID of the user whose preferences we're updating.
        :param body: A dictionary of preference values.
        """

        if request.current_user_id != user_id:
            abort(403, _("You can't change preferences of other users."))

        return user_api.user_update_preferences(user_id, body)
