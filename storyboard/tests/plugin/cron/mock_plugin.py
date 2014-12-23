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

from oslo.config import cfg

import storyboard.plugin.cron.base as plugin_base


CONF = cfg.CONF


class MockPlugin(plugin_base.CronPluginBase):
    """A mock cron plugin for testing."""

    def __init__(self, config, is_enabled=True,
                 plugin_interval="0 0 1 1 0"):
        """Create a new instance of the base plugin, with some sane defaults.
        The default cron interval is '0:00 on January 1st if a Sunday', which
        should ensure that the manipulation of the cron environment on the test
        machine does not actually execute anything.
        """
        super(MockPlugin, self).__init__(config)
        self.is_enabled = is_enabled
        self.plugin_interval = plugin_interval

    def enabled(self):
        """Return our enabled value."""
        return self.is_enabled

    def run(self, start_time, end_time):
        """Stores the data to a global variable so we can test it.

        :param working_dir: Path to a working directory your plugin can use.
        :param start_time: The last time the plugin was run.
        :param end_time: The current timestamp.
        :return: Nothing.
        """
        self.last_invocation_parameters = (start_time, end_time)

    def interval(self):
        """The plugin's cron interval, as a string.

        :return: The cron interval. Example: "* * * * *"
        """
        return self.plugin_interval
