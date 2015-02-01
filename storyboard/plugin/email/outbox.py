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

import mailbox
import os
import six
import time
import uuid

from oslo.config import cfg
from oslo_log import log

from storyboard.plugin.email import get_email_directory


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class get_outbox(object):
    """This generator will create an instance of the email outbox, and make
    sure it has been closed after use.
    """

    def __init__(self):
        self.outbox = None

    def __enter__(self):
        self.outbox = Outbox()
        return self.outbox

    def __exit__(self, exc_type, exc_val, exc_tb):
        # On a clean use, flush the outbox.
        if not exc_type:
            self.outbox.flush()

        # All outboxes get closed.
        self.outbox.close()
        self.outbox = None


class Outbox(mailbox.Maildir):
    """Our email outbox, a place where we store our generated email messages
    before our cron mailer sends them out. It is implemented using the python
    email.Maildir package, because, well, it quacks like a mailbox.
    """

    def __init__(self):
        """Create a new instance of our outbox."""
        working_directory = get_email_directory()
        outbox_path = os.path.join(working_directory, 'outbox')

        # Explicitly set the factory to None, because py2.7 defaults this to
        # rfc822, which causes the return types to be different between 3.4
        # and 2.7.
        mailbox.Maildir.__init__(self, outbox_path, factory=None)

    def _create_tmp(self):
        """Create a file in the tmp subdirectory and open and return it. This
        is an intentional override of the parent class, in an attempt to
        overcome the pid-based name generator that might cause conflicts when
        there are two operating threads in a single pid.
        """
        now = time.time()
        uniq = six.text_type(uuid.uuid4())
        uniq = "%sM%s_%s" % (int(now), int(now % 1 * 1e6), uniq)
        path = os.path.join(self._path, 'tmp', uniq)

        return mailbox._create_carefully(path)
