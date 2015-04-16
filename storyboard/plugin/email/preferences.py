# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

from storyboard.plugin.email.base import EmailPluginBase
from storyboard.plugin.user_preferences import UserPreferencesPluginBase


class EmailPreferences(UserPreferencesPluginBase, EmailPluginBase):
    def get_default_preferences(self):
        """Defines plugin preferences that may be set by the user.

        Preferences are as follows: Do you want email? Would you prefer
        individual or a digest? And if a digest, at what time of the day do
        you want it (as seconds_past_midnight UTC)?

        :return: Preferences for the email plugin.
        """

        return {
            'plugin_email_enable': False,
            'plugin_email_digest': False,
            'plugin_email_digest_time': 8 * 60 * 60
        }
