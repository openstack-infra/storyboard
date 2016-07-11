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

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class get_smtp_client(object):
    """This will construct an SMTP client given the options configured
    in storyboard.conf, and return it. If authentication options are
    provided, it will attempt to use these to connect to the server.
    """

    def __enter__(self):
        email_config = CONF.plugin_email

        # SSL or not SSL?
        if not email_config.smtp_ssl_certfile \
                or not email_config.smtp_ssl_keyfile:
            self.s = smtplib.SMTP(
                host=email_config.smtp_host,
                port=email_config.smtp_port,
                local_hostname=email_config.smtp_local_hostname,
                timeout=email_config.smtp_timeout)
        else:
            self.s = smtplib.SMTP_SSL(
                host=email_config.smtp_host,
                port=email_config.smtp_port,
                keyfile=email_config.smtp_ssl_keyfile,
                certfile=email_config.smtp_ssl_certfile,
                local_hostname=email_config.smtp_local_hostname,
                timeout=email_config.smtp_timeout)

        # Do we need to log in?
        if email_config.smtp_user and email_config.smtp_password:
            self.s.login(email_config.smtp_user,
                         email_config.smtp_password)

        return self.s

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.s.quit()
