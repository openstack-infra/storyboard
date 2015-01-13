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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from datetime import timedelta

import storyboard.db.api.base as api_base
from storyboard.db.models import AccessToken
from storyboard.plugin.cron.base import CronPluginBase


class TokenCleaner(CronPluginBase):
    """A Cron Plugin which checks periodically for expired auth tokens and
    removes them from the database. By default it only cleans up expired
    tokens that are more than a week old, to permit some historical debugging
    forensics.
    """

    def enabled(self):
        """Indicate whether this plugin is enabled. This indicates whether
        this plugin alone is runnable, as opposed to the entire cron system.
        """
        return True

    def interval(self):
        """This plugin executes on startup, and once every hour after that.

        :return: "? * * * *"
        """
        return "? * * * *"

    def run(self, start_time, end_time):
        """Remove all oauth tokens that are more than a week old.

        :param start_time: The last time the plugin was run.
        :param end_time: The current timestamp.
        """
        # Calculate last week.
        lastweek = datetime.utcnow() - timedelta(weeks=1)

        # Build the query.
        query = api_base.model_query(AccessToken)

        # Apply the filter.
        query = query.filter(AccessToken.expires_at < lastweek)

        # Batch delete.
        query.delete()
