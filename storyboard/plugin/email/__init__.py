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

from oslo_config import cfg
from oslo_log import log

from storyboard.common.working_dir import get_plugin_directory


CONF = cfg.CONF
LOG = log.getLogger(__name__)

PLUGIN_OPTS = [
    cfg.BoolOpt("enable",
                default=False,
                help="Enable, or disable, the notification email plugin."),
    cfg.StrOpt("sender",
               default='StoryBoard (Do Not Reply)'
                       '<do_not_reply@storyboard.openstack.org>',
               help="The email address from which storyboard will send its "
                    "messages."),
    cfg.StrOpt("reply_to",
               default=None,
               help="The email address of the Reply-To header (optional)."),
    cfg.StrOpt("default_url",
               default=None,
               help="The default/fallback url base to use in emails."),
    cfg.StrOpt("smtp_host",
               default='localhost',
               help="The SMTP server to use."),
    cfg.IntOpt("smtp_port",
               default=25,
               help="The SMTP Server Port to connect to (default 25)."),
    cfg.IntOpt("smtp_timeout",
               default=10,
               help="Timeout, in seconds, to wait for the SMTP connection to "
                    "fail"),
    cfg.StrOpt("smtp_local_hostname",
               default=None,
               help="The FQDN of the sending host when identifying itself "
                    "to the SMTP server (optional)."),
    cfg.StrOpt("smtp_ssl_keyfile",
               default=None,
               help="Path to the SSL Keyfile, when using ESMTP. Please make "
                    "sure the storyboard client can read this file."),
    cfg.StrOpt("smtp_ssl_certfile",
               default=None,
               help="Path to the SSL Certificate, when using ESMTP "
                    "(optional). Please make sure the storyboard client can "
                    "read this file."),
    cfg.StrOpt("smtp_user",
               default=None,
               help="Username/login for the SMTP server."),
    cfg.StrOpt("smtp_password",
               default=None,
               help="Password for the SMTP server.")
]

CONF.register_opts(PLUGIN_OPTS, "plugin_email")


def get_email_directory():
    """A shared utility method that always provides the same working
    directory. Error handling is explicitly not provided, as the methods used
    'should' be consistent about the errors they themselves raise.
    """
    return get_plugin_directory("email")
