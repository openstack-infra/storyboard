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

import email
from mock import patch
from random import random
import smtplib

from oslo.config import cfg

from storyboard.plugin.email.factory import EmailFactory
from storyboard.plugin.email.outbox import Outbox
from storyboard.plugin.email.workers import EmailSender
from storyboard.tests import base


CONF = cfg.CONF


class TestEmailSender(base.WorkingDirTestCase):
    """Test the email sender plugin. Makes use of the dummy smtp sender."""

    def setUp(self):
        """Add messages to the outbox. Note that the outbox directory will be
        deleted when the working directory is cleared in the parent test class.
        """
        super(TestEmailSender, self).setUp()

        # Build a test outbox.
        outbox = Outbox()
        self.assertIsNotNone(outbox)

        factory = EmailFactory('test@example.org',
                               'test_subject',
                               'test.txt',
                               'plugin.email')
        # Generate 25 emails that are now-ish
        for i in range(0, 25):
            recipient = 'test_%s@example.com' % (i,)
            message = factory.build(recipient, test_parameter=i)
            outbox.add(message)

        # Generate 25 emails that are in the 0-60 timeframe.
        for i in range(0, 25):
            recipient = 'test_%s@example.com' % (i,)
            message = factory.build(recipient, test_parameter=i)

            # Override the date header with our actual date + some random
            # seconds, so that all timestamps fall between 1 and 59
            message.replace_header('Date',
                                   email.utils.formatdate(1 + (random() * 58)))
            outbox.add(message)
        outbox.flush()

    def test_trigger(self):
        """Assert that the this plugin runs every minute."""
        plugin = EmailSender(CONF)
        trigger = plugin.trigger()

        self.assertEqual(60, trigger.interval_length)

    @patch('storyboard.plugin.email.workers.get_smtp_client')
    def test_failing_sender_causes_flush(self, get_smtp_client):
        """Assert that running against a failing sender causes no errors,
        and discards all messages, so we don't build up a massive send queue.
        """

        # Raise an exception when this is called.
        get_smtp_client.side_effect = smtplib.SMTPException

        # Run the plugin.
        plugin = EmailSender(CONF)
        plugin.run()

        # Read the outbox, making sure there's no messages left.
        outbox = Outbox()
        self.assertEqual(0, len(outbox))

    @patch('mock_smtp.DummySMTP.sendmail')
    def test_successful_run(self, mock_sendmail):
        """Assert that running with a valid sender and outbox sends all the
        messages in the provided time frame, and leaves other messages alone.
        """

        # Run the plugin.
        plugin = EmailSender(CONF)
        plugin.run()

        # The outbox should be clean.
        outbox = Outbox()
        self.assertEqual(0, len(outbox))

        # The dummy SMTP library should have received 50 messages.
        self.assertEqual(50, mock_sendmail.call_count)

    @patch('mock_smtp.DummySMTP.sendmail')
    def test_badly_formatted_email_causes_flush(self, mock_sendmail):
        """Assert that a message that would otherwise cause a send exceptoin
        creates no side_effect, and flushes the message from the queue.
        """

        # Create a sideffect
        mock_sendmail.side_effect = smtplib.SMTPException

        # Run the plugin.
        plugin = EmailSender(CONF)
        plugin.run()

        # Read the outbox, making sure that all messages have been flushed.
        outbox = Outbox()
        self.assertEqual(0, len(outbox))

        # Assert that the sendmail message was called 50 times.
        self.assertEqual(50, mock_sendmail.call_count)

    @patch('storyboard.plugin.email.workers.get_outbox')
    def test_failing_outbox_causes_no_side_effects(self, mock_get_outbox):
        """Assert that running with a valid sender but invalid outbox does
        nothing, since we can't get at any messages.
        """

        # Raise an exception when this is called.
        mock_get_outbox.side_effect = OSError

        # Run the plugin.
        plugin = EmailSender(CONF)
        plugin.run()

        # Read the outbox, making sure we still have 50 messages (since the
        # outbox was never accessible via the context handler.
        outbox = Outbox()
        self.assertEqual(50, len(outbox))
