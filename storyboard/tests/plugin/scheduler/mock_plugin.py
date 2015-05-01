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

import datetime

from apscheduler.triggers.date import DateTrigger
from oslo_config import cfg

import storyboard.plugin.scheduler.base as plugin_base

CONF = cfg.CONF
one_year_from_now = datetime.datetime.now() + datetime.timedelta(days=365)
test_trigger = DateTrigger(run_date=one_year_from_now)


class MockPlugin(plugin_base.SchedulerPluginBase):
    """A mock scheduler plugin for testing."""

    def __init__(self, config, is_enabled=True,
                 trigger=test_trigger):
        """Create a new instance of the base plugin, with some sane defaults
        and a time interval that will never execute.
        """
        super(MockPlugin, self).__init__(config)
        self.is_enabled = is_enabled
        self.run_invoked = False
        self._trigger = trigger

    def enabled(self):
        """Return our enabled value."""
        return self.is_enabled

    def run(self):
        """Stores the data to a global variable so we can test it.
        """
        self.run_invoked = True

    def trigger(self):
        """The plugin's trigger."""
        return self._trigger
