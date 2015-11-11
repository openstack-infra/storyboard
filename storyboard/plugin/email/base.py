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


import smtplib

from oslo_config import cfg
from oslo_log import log

from storyboard.plugin.base import PluginBase
from storyboard.plugin.email import get_email_directory
from storyboard.plugin.email.smtp_client import get_smtp_client

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class EmailPluginBase(PluginBase):
    """Base class for all email plugins."""

    def enabled(self):
        """Indicate whether the email plugin system is enabled. It checks for
        all the necessary configuration options that are required.
        """

        # Assert that the configuration is set to enabled.
        email_config = CONF.plugin_email
        if not email_config.enable:
            return False

        # Assert that we can generate a working directory.
        try:
            get_email_directory()
        except IOError as e:
            LOG.error('Cannot create working directory, disabling plugin: %s' %
                      (e,))
            return False

        # Assert that the smtp sender can connect to the server.
        try:
            with get_smtp_client():
                pass
        except smtplib.SMTPException as e:
            LOG.error('Cannot contact SMTP server, disabling plugin: %s' %
                      (e,))
            return False

        # Looks like we have all we need.
        return True
