# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import calendar
import datetime
import os
import pytz
import shutil
import tzlocal

import storyboard.common.working_dir as w_dir
import storyboard.tests.base as base
from storyboard.tests.plugin.cron.mock_plugin import MockPlugin


class TestCronPluginBase(base.TestCase):
    """Test the abstract plugin core."""

    def setUp(self):
        super(TestCronPluginBase, self).setUp()

        # Create the stamp directory
        cron_directory = w_dir.get_plugin_directory('cron')
        if not os.path.exists(cron_directory):
            os.makedirs(cron_directory)

    def tearDown(self):
        super(TestCronPluginBase, self).tearDown()

        # remove the stamp directory
        cron_directory = w_dir.get_plugin_directory('cron')
        shutil.rmtree(cron_directory)

    def test_get_name(self):
        """Test that the plugin can name itself."""
        plugin = MockPlugin(dict())
        self.assertEqual("storyboard.tests.plugin.cron.mock_plugin:MockPlugin",
                         plugin.get_name())

    def test_mtime(self):
        """Assert that the mtime utility function always returns UTC dates,
        yet correctly translates dates to systime.
        """
        sys_tz = tzlocal.get_localzone()

        # Generate the plugin and build our file path
        plugin = MockPlugin(dict())
        plugin_name = plugin.get_name()
        cron_directory = w_dir.get_plugin_directory('cron')
        last_run_path = os.path.join(cron_directory, plugin_name)

        # Call the mtime method, ensuring that it is created.
        self.assertFalse(os.path.exists(last_run_path))
        creation_mtime = plugin._get_file_mtime(last_run_path)
        self.assertTrue(os.path.exists(last_run_path))

        # Assert that the returned timezone is UTC.
        self.assertEquals(pytz.utc, creation_mtime.tzinfo)

        # Assert that the creation time equals UTC 0.
        creation_time = calendar.timegm(creation_mtime.timetuple())
        self.assertEqual(0, creation_time.real)

        # Assert that we can update the time.
        updated_mtime = datetime.datetime(year=2000, month=1, day=1, hour=1,
                                          minute=1, second=1, tzinfo=pytz.utc)
        updated_result = plugin._get_file_mtime(last_run_path, updated_mtime)
        self.assertEqual(updated_mtime, updated_result)
        updated_stat = os.stat(last_run_path)
        updated_time_from_file = datetime.datetime \
            .fromtimestamp(updated_stat.st_mtime, tz=sys_tz)
        self.assertEqual(updated_mtime, updated_time_from_file)

        # Assert that passing a system timezone datetime is still applicable
        # and comparable.
        updated_sysmtime = datetime.datetime(year=2000, month=1, day=1, hour=1,
                                             minute=1, second=1,
                                             tzinfo=sys_tz)
        updated_sysresult = plugin._get_file_mtime(last_run_path,
                                                   updated_sysmtime)
        self.assertEqual(updated_sysmtime, updated_sysresult)
        self.assertEqual(pytz.utc, updated_sysresult.tzinfo)

    def test_execute(self):
        """Assert that the public execution method correctly builds the
        plugin API's input parameters.
        """

        # Generate the plugin and simulate a previous execution
        plugin = MockPlugin(dict())
        plugin_name = plugin.get_name()
        cron_directory = w_dir.get_plugin_directory('cron')

        last_run_path = os.path.join(cron_directory, plugin_name)
        last_run_date = datetime.datetime(year=2000, month=1, day=1,
                                          hour=12, minute=0, second=0,
                                          microsecond=0, tzinfo=pytz.utc)
        plugin._get_file_mtime(last_run_path, last_run_date)

        # Execute the plugin
        plugin.execute()

        # Current timestamp, remove microseconds so that we don't run into
        # execution time delay problems.
        now = pytz.utc.localize(datetime.datetime.utcnow()) \
            .replace(microsecond=0)

        # Check the plugin's params.
        self.assertEqual(last_run_date, plugin.last_invocation_parameters[0])
        self.assertEqual(now, plugin.last_invocation_parameters[1])
