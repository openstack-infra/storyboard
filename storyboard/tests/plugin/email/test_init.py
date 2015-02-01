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

from oslo.config import cfg

from storyboard.tests import base


CONF = cfg.CONF


class TestConfiguration(base.TestCase):
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
