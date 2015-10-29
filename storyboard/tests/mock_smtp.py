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
import socket

# Store this here before we monkeypatch it.
OLD_SMTP = smtplib.SMTP


class DummySMTP(OLD_SMTP):
    """A Mock SMTP library that intercepts most calls to the underlying
    library and exposes the parameters to the test methods.
    """

    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        OLD_SMTP.__init__(self, host, port, local_hostname, timeout)
        self.sendmail_invoked = 0
        if hasattr(self, 'exception'):
            raise self.exception()

    def connect(self, host='localhost', port=0):
        self.host = host
        self.port = port
        self.is_connected = True

        return (220, 'EHLO')

    def login(self, username, password):
        self.username = username
        self.password = password

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[],
                 rcpt_options=[]):
        self.sendmail_invoked += 1
        self.from_addr = from_addr
        self.to_addr = to_addrs
        self.msg = msg
        self.mail_options = mail_options
        self.rcpt_options = rcpt_options

    def quit(self):
        self.has_quit = True


class DummySMTP_SSL(DummySMTP):
    """A Mock SSL SMTP library that intercepts most calls to the underlying
    library and exposes the parameters to the test methods.
    """

    def __init__(self, host='', port=0, local_hostname=None,
                 keyfile=None, certfile=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.keyfile = keyfile
        self.certfile = certfile
        DummySMTP.__init__(self, host, port, local_hostname, timeout)

    def _get_socket(self, host, port, timeout):
        return None

# Monkeypatch our SMTP Instances.
smtplib.SMTP = DummySMTP
smtplib.SMTP_SSL = DummySMTP_SSL
