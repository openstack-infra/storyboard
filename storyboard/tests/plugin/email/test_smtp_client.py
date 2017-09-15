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

from storyboard.plugin.email.smtp_client import get_smtp_client
from storyboard.tests import base
from storyboard.tests import mock_smtp as mock


CONF = cfg.CONF


class TestGetSender(base.TestCase):
    def setup_config(self, host='localhost', port=25, timeout=10,
                     local_hostname=None, ssl_keyfile=None,
                     ssl_certfile=None, user=None, password=None):
        CONF.set_override('smtp_host', host, 'plugin_email')
        CONF.set_override('smtp_port', port, 'plugin_email')
        CONF.set_override('smtp_timeout', timeout, 'plugin_email')
        CONF.set_override('smtp_local_hostname', local_hostname,
                          'plugin_email')
        CONF.set_override('smtp_ssl_keyfile', ssl_keyfile, 'plugin_email')
        CONF.set_override('smtp_ssl_certfile', ssl_certfile, 'plugin_email')
        CONF.set_override('smtp_user', user, 'plugin_email')
        CONF.set_override('smtp_password', password, 'plugin_email')

    def clear_config(self):
        CONF.clear_override('smtp_host', 'plugin_email')
        CONF.clear_override('smtp_port', 'plugin_email')
        CONF.clear_override('smtp_timeout', 'plugin_email')
        CONF.clear_override('smtp_local_hostname', 'plugin_email')
        CONF.clear_override('smtp_ssl_keyfile', 'plugin_email')
        CONF.clear_override('smtp_ssl_certfile', 'plugin_email')
        CONF.clear_override('smtp_user', 'plugin_email')
        CONF.clear_override('smtp_password', 'plugin_email')

    def setUp(self):
        """Clear configuration overrides."""
        super(TestGetSender, self).setUp()

        self.addCleanup(self.clear_config)

    def test_simple_build(self):
        """Assert a simple sender get, make sure that configuration elements
        are properly passed through.
        """
        self.setup_config(host='localhost', port=25, timeout=42,
                          local_hostname='localhost', user='test_user',
                          password='test_password')

        with get_smtp_client() as smtp_client:
            self.assertIsInstance(smtp_client, mock.DummySMTP)

            self.assertEqual('localhost', smtp_client.host)
            self.assertEqual(25, smtp_client.port)
            self.assertTrue(smtp_client.is_connected)
            self.assertEqual(42, smtp_client.timeout)
            self.assertEqual('localhost', smtp_client.local_hostname)
            self.assertEqual(smtp_client.username, 'test_user')
            self.assertEqual(smtp_client.password, 'test_password')

        self.clear_config()

    def test_ssl_build(self):
        """Assert a simple ssl sender get, make sure that configuration
        elements are properly passed through.
        """
        self.setup_config(host='localhost', port=25, timeout=42,
                          local_hostname='localhost',
                          ssl_keyfile='/tmp/ssl.key',
                          ssl_certfile='/tmp/ssl.cert', user='test_user',
                          password='test_password')

        with get_smtp_client() as smtp_client:
            self.assertIsInstance(smtp_client, mock.DummySMTP_SSL)

            self.assertEqual('localhost', smtp_client.host)
            self.assertEqual(25, smtp_client.port)
            self.assertTrue(smtp_client.is_connected)
            self.assertEqual(42, smtp_client.timeout)
            self.assertEqual(smtp_client.keyfile, '/tmp/ssl.key')
            self.assertEqual(smtp_client.certfile, '/tmp/ssl.cert')
            self.assertEqual(smtp_client.username, 'test_user')
            self.assertEqual(smtp_client.password, 'test_password')

        self.clear_config()

    def test_quit(self):
        """Assert that quit is called."""
        self.setup_config(host='localhost', port=25, timeout=42,
                          local_hostname='localhost', user='test_user',
                          password='test_password')

        with get_smtp_client() as smtp_client:
            pass

        self.assertTrue(smtp_client.has_quit)
        self.clear_config()
