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


import datetime
from email.message import Message
from mock import patch
import re
import six
import uuid

from oslo.config import cfg

from storyboard.plugin.email.factory import EmailFactory
from storyboard.plugin.email.outbox import get_outbox
from storyboard.plugin.email.outbox import Outbox
from storyboard.tests import base


CONF = cfg.CONF


class TestGetOutbox(base.WorkingDirTestCase):
    def test_single_scope(self):
        """Assert that get_outbox returns an Outbox. This test brought to you
        by the department of redundancy department.
        """
        with get_outbox() as outbox:
            self.assertIsInstance(outbox, Outbox)

    @patch.object(Outbox, 'close')
    def test_was_closed(self, mock_close):
        """Assert that the close() method is called when the scope exits."""
        with get_outbox():
            pass

        self.assertTrue(mock_close.called)

    @patch.object(Outbox, 'flush')
    def test_was_flushed(self, mock_flush):
        """Assert that the flush() method is called when the scope exits."""
        with get_outbox():
            pass

        self.assertTrue(mock_flush.called)


class TestOutbox(base.WorkingDirTestCase):
    def test_create_outbox(self):
        '''Assert that we can create an outbox. At this point, given all of
        the other IOError and working directory checks, we are not bothering
        with additional sanity checks to make sure the outbox can be created.
        If things are broken at this point, it should have already gotten
        picked up.
        '''
        outbox = Outbox()
        self.assertIsNotNone(outbox)

    def test_basic_outbox_functions(self):
        '''Assert that we can list elements of our outbox.'''
        outbox = Outbox()
        self.assertIsNotNone(outbox)

        factory = EmailFactory('test@example.org',
                               'test_subject',
                               'test.txt',
                               'plugin.email')
        for i in range(0, 100):
            recipient = 'test_%s@example.com' % (i,)
            message = factory.build(recipient, test_parameter=i)

            # This will throw an error if the message ID already exists.
            outbox.add(message)
        outbox.flush()

        values = []
        for key, email in six.iteritems(outbox):
            # Assert that the type of the email is correct.
            self.assertIsInstance(email, Message)

            # Assert that the message has a date header. While we can extract
            # this from the ID, it's also helpful for us to timebox the
            # emails to send by worker.
            self.assertIsNotNone(email.get('Date'))

            # Make sure we only have one payload (since that's what the
            # factory was configured with)
            self.assertEqual(1, len(email.get_payload()))

            # Pull the ID from the payload and check it against all the
            # emails we've found so far.
            text_part = email.get_payload(0)
            key = int(text_part.get_payload(decode=True))
            self.assertNotIn(key, values)

            # Store the key for later comparison.
            values.append(key)

        self.assertEqual(100, len(values))

    def test_uuid_ids(self):
        '''Assert that our message id's are not thread-based.'''
        outbox = Outbox()
        self.assertIsNotNone(outbox)

        factory = EmailFactory('test@example.org',
                               'test_subject',
                               'test.txt',
                               'plugin.email')
        for i in range(0, 100):
            recipient = 'test_%s@example.com' % (i,)
            message = factory.build(recipient, test_parameter=i)

            # This will throw an error if the message ID already exists.
            key = outbox.add(message)
            parts = re.match(r'^([0-9]+)M([0-9]+)_(.*)$', key)
            self.assertIsNotNone(parts)

            # The first part should be a timestamp.
            timestamp = float(parts.group(1)) + (float(parts.group(2)) / 1e6)
            send_date = datetime.datetime.fromtimestamp(timestamp)
            self.assertIsNotNone(send_date)

            # The last part should be a UUID. Trying to construct it will
            # cause a value error if it is not.
            uuid.UUID(parts.group(3), version=4)

        outbox.flush()
