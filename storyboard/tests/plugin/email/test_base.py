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
import shutil
import smtplib
import stat

from oslo_config import cfg

from storyboard.plugin.email.base import EmailPluginBase
from storyboard.tests import base
from storyboard.tests import mock_smtp as mock


CONF = cfg.CONF
PERM_READ_ONLY = stat.S_IRUSR + stat.S_IRGRP + stat.S_IROTH
PERM_ALL = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO


class TestEmailPluginBase(base.WorkingDirTestCase):
    """Unit tests for the base email plugin."""

    def setup_helper(self, config=True, working_dir=True, smtp=True):
        """Setup helper: Setup the email test environment with various items
        enabled/disabled.
        """
        CONF.set_override('enable', config, 'plugin_email')

        if not working_dir:
            os.chmod(CONF.working_directory, PERM_READ_ONLY)

        if not smtp:
            mock.DummySMTP.exception = smtplib.SMTPException

        self.addCleanup(self._clear_setup)

    def _clear_setup(self):
        if os.path.exists(CONF.working_directory):
            os.chmod(CONF.working_directory, PERM_ALL)
            shutil.rmtree(CONF.working_directory)

        if hasattr(mock.DummySMTP, 'exception'):
            delattr(mock.DummySMTP, 'exception')

    def test_all_systems_go(self):
        """Assert that if we can get a working directory, and we can get an
        email sender, and we have the configuration enabled, that we are
        enabled.
        """
        self.setup_helper()
        plugin = EmailPluginBase(CONF)
        self.assertTrue(plugin.enabled())

    def test_no_config(self):
        """Assert that we're not enabled when the configuration says we're
        not.
        """
        self.setup_helper(config=False)
        plugin = EmailPluginBase(CONF)
        self.assertFalse(plugin.enabled())

    def test_no_working_dir(self):
        """Assert that we're not enabled when the working directory is not
        accessible.
        """
        self.setup_helper(working_dir=False)
        plugin = EmailPluginBase(CONF)
        self.assertFalse(plugin.enabled())

    def test_no_smtp(self):
        """Assert that we're not enabled when smtp is misconfigured.
        """
        self.setup_helper(smtp=False)
        plugin = EmailPluginBase(CONF)
        self.assertFalse(plugin.enabled())
