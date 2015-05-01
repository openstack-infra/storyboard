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

import os
import stat

from oslo_config import cfg

from storyboard.plugin.email import get_email_directory
from storyboard.tests import base


CONF = cfg.CONF


class TestEmailConfiguration(base.TestCase):
    def test_configuration_defaults(self):
        self.assertIsNotNone(CONF.plugin_email)

        conf = CONF.plugin_email

        self.assertEqual('localhost', conf.smtp_host)
        self.assertEqual(25, conf.smtp_port)
        self.assertEqual(10, conf.smtp_timeout)
        self.assertEqual(None, conf.smtp_local_hostname)
        self.assertEqual(None, conf.smtp_ssl_keyfile)
        self.assertEqual(None, conf.smtp_ssl_certfile)
        self.assertEqual(None, conf.smtp_user)
        self.assertEqual(None, conf.smtp_password)


class TestGetEmailDirectory(base.WorkingDirTestCase):
    def test_get_email_directory(self):
        """Can we resolve the email directory? Most of this testing also
        exists in test_working_dir, however it behooves us to test it here as
        well.
        """
        expected_path = os.path.realpath(os.path.join(CONF.working_directory,
                                                      'plugin', 'email'))
        self.assertFalse(os.path.exists(expected_path))

        resolved_path = get_email_directory()

        self.assertEqual(expected_path, resolved_path)
        self.assertTrue(os.path.exists(CONF.working_directory))
        self.assertTrue(os.path.exists(expected_path))

        self.assertTrue(os.access(CONF.working_directory, os.W_OK))
        self.assertTrue(os.access(expected_path, os.W_OK))

    def test_get_email_directory_not_creatable(self):
        """Assert that the get_email_directory() method raises an error if
        it cannot be created.
        """

        # Set the permissions
        os.chmod(CONF.working_directory,
                 stat.S_IRUSR + stat.S_IRGRP + stat.S_IROTH)

        # Make sure it raises an exception.
        self.assertRaises(IOError, get_email_directory)
