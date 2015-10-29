# -*- encoding: utf-8 -*-
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

import six

from jinja2.exceptions import TemplateNotFound

from storyboard.plugin.email.factory import EmailFactory
from storyboard.tests import base


class TestEmailFactory(base.TestCase):
    def test_simple_build(self):
        """Assert that a simple build provides an email.
        """
        factory = EmailFactory('test@example.org',
                               'test_subject.txt',
                               'test.txt',
                               'plugin.email')

        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')

        # Assert that the message is multipart
        self.assertTrue(msg.is_multipart())
        self.assertEqual(1, len(msg.get_payload()))

        # Test message headers
        self.assertEqual('test@example.org', msg.get('From'))
        self.assertEqual('test_recipient@example.org', msg.get('To'))
        self.assertEqual('value', msg.get('Subject'))
        self.assertEqual('auto-generated', msg.get('Auto-Submitted'))
        self.assertEqual('multipart/alternative', msg.get('Content-Type'))
        self.assertIsNotNone(msg.get('Date'))  # This will vary

        payload_text = msg.get_payload(0)
        self.assertEqual('text/plain; charset="utf-8"',
                         payload_text.get('Content-Type'))
        self.assertEqual(b'value',
                         payload_text.get_payload(decode=True))

        # Assert that there's only one payload.
        self.assertEqual(1, len(msg.get_payload()))

    def test_custom_headers(self):
        """Assert that we can set custom headers."""

        factory = EmailFactory('test@example.org',
                               'test_subject.txt',
                               'test.txt',
                               'plugin.email')
        custom_headers = {
            'X-Custom-Header': 'test-header-value'
        }
        for name, value in six.iteritems(custom_headers):
            factory.add_header(name, value)

        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')
        self.assertEqual('test-header-value',
                         msg.get('X-Custom-Header'))

        # test that headers may be overridden, and that we don't end up with
        # duplicate subjects.
        factory.add_header('Subject', 'new_subject')
        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')
        self.assertEqual('new_subject', msg.get('Subject'))

    def test_subject_template(self):
        """Assert that the subject is templateable."""

        factory = EmailFactory('test@example.org',
                               'test_subject.txt',
                               'test.txt',
                               'plugin.email')
        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')
        self.assertEqual('value', msg.get('Subject'))

        # Assert that the subject is trimmed. and appended with an ellipsis.
        factory = EmailFactory('test@example.org',
                               'test_long_subject.txt',
                               'test.txt',
                               'plugin.email')
        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')
        self.assertEqual(78, len(msg.get('Subject')))
        self.assertEqual('...', msg.get('Subject')[-3:])

        # Assert that the subject has newlines trimmed
        factory = EmailFactory('test@example.org',
                               'test_subject_newline.txt',
                               'test.txt',
                               'plugin.email')
        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')
        self.assertEqual('with newline', msg.get('Subject'))

    def test_html_template(self):
        '''Assert that we may add an additional text template to the email
        engine.
        '''

        factory = EmailFactory('test@example.org',
                               'test_subject.txt',
                               'test.txt',
                               'plugin.email')
        factory.add_text_template('test.html', 'html')

        msg = factory.build('test_recipient@example.org',
                            test_parameter='value')

        # Assert that the message is multipart
        self.assertTrue(msg.is_multipart())
        self.assertEqual(2, len(msg.get_payload()))

        payload_text = msg.get_payload(0)
        self.assertEqual('text/plain; charset="utf-8"',
                         payload_text.get('Content-Type'))
        self.assertEqual(b'value',
                         payload_text.get_payload(decode=True))

        payload_html = msg.get_payload(1)
        self.assertEqual('text/html; charset="utf-8"',
                         payload_html.get('Content-Type'))
        self.assertEqual(b'value',
                         payload_html.get_payload(decode=True))

    def test_no_template(self):
        """Assert that attempting to load an invalid template raises an
        exception.
        """
        try:
            EmailFactory('test@example.org',
                         'invalid_subject.txt',
                         'invalid.txt',
                         'plugin.email')
            self.assertFalse(True)
        except TemplateNotFound:
            self.assertFalse(False)

        try:
            factory = EmailFactory('test@example.org',
                                   'test_subject.txt',
                                   'test.txt',
                                   'plugin.email')
            factory.add_text_template('invalid.html', 'html')
            self.assertFalse(True)
        except TemplateNotFound:
            self.assertFalse(False)
