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


import pytz
import smtplib

from apscheduler.triggers.interval import IntervalTrigger
from oslo_log import log

from storyboard.plugin.email.base import EmailPluginBase
from storyboard.plugin.email.outbox import get_outbox
from storyboard.plugin.email.smtp_client import get_smtp_client
from storyboard.plugin.scheduler.base import SchedulerPluginBase

LOG = log.getLogger(__name__)


class EmailSender(SchedulerPluginBase, EmailPluginBase):
    """A Cron Plugin which goes through all email messages that have been
    written to the outbox in its provided time interval, and sends them using
    the email sender.
    """

    def trigger(self):
        """This plugin executes every minute. APScheduler will collate the
        executions of this plugin, so there will be no overlap between
        executions.
        """
        return IntervalTrigger(minutes=1, timezone=pytz.utc)

    def run(self):
        """Send all the messages between the given timestamps. If a message
        cannot be sent, or if the sender is not retrievable,
        then discard all messages - we don't want to build up a massive
        backlog and then spam people.
        """

        # Try to send email.
        try:
            with get_outbox() as outbox:
                with get_smtp_client() as smtp_client:
                    for key, message in outbox.iteritems():
                        from_addr = message.get('From')
                        to_addrs = message.get('To')

                        try:
                            smtp_client.sendmail(from_addr=from_addr,
                                                 to_addrs=to_addrs,
                                                 msg=message.as_string())
                        except smtplib.SMTPException as e:
                            LOG.error(
                                'Cannot send email, discarding: %s' % (e,))
                        finally:
                            outbox.discard(key)
        except Exception as e:
            LOG.error("Error while trying to send email.")
            LOG.error(e)

        # After everything's said and done, clear out anything that hasn't
        # been handled.
        try:
            with get_outbox() as outbox:
                for key, message in outbox.iteritems():
                    outbox.discard(key)
        except Exception as e:
            LOG.error("Unable to flush remaining emails.", e)
