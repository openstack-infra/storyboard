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
from oslo_log import log
import pytz

from apscheduler.triggers.interval import IntervalTrigger

import storyboard.db.api.base as api_base
from storyboard.db.models import AccessToken
from storyboard.plugin.scheduler.base import SchedulerPluginBase

LOG = log.getLogger(__name__)


class TokenCleaner(SchedulerPluginBase):
    """A Cron Plugin which checks periodically for expired auth tokens and
    removes them from the database. By default it only cleans up expired
    tokens that are more than a week old, to permit some historical debugging
    forensics.
    """

    def enabled(self):
        """Indicate whether this plugin is enabled. This indicates whether
        this plugin alone is runnable, as opposed to the entire cron system.
        """
        if 'plugin_token_cleaner' in self.config:
            return self.config.plugin_token_cleaner.enable or False
        return False

    def trigger(self):
        """This plugin executes every hour."""
        return IntervalTrigger(hours=1, timezone=pytz.utc)

    def run(self):
        """Remove all oauth tokens that are more than a week old.
        """
        # Calculate last week.
        lastweek = datetime.now(pytz.utc) - timedelta(weeks=1)
        LOG.debug("Removing Expired OAuth Tokens: %s" % (lastweek,))

        # Build the session.
        session = api_base.get_session(in_request=False,
                                       autocommit=False,
                                       expire_on_commit=True)
        try:
            query = api_base.model_query(AccessToken, session)

            # Apply the filter.
            query = query.filter(AccessToken.expires_at < lastweek)

            # Manually deleting each record, because batch deletes are an
            # exception to ORM Cascade markup.
            for token in query.all():
                session.delete(token)

            session.commit()
        except Exception:
            session.rollback()
