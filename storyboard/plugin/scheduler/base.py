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


import abc
import six

from oslo_log import log

import storyboard.plugin.base as plugin_base


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class SchedulerPluginBase(plugin_base.PluginBase):
    """Base class for a plugin that executes business logic on a schedule.
    All plugins are loaded into the scheduler in such a way that long-running
    plugins will not cause multiple 'overlapping' executions.
    """

    @abc.abstractmethod
    def run(self):
        """Execute a periodic task. It is guaranteed that no more than one of
        these will be run on any one storyboard instance. If you are running
        multiple instances, that is not the case.
        """

    @abc.abstractmethod
    def trigger(self):
        """The plugin's scheduler trigger. Must implement BaseTrigger from
        the apscheduler package.

        :return: A trigger that describes the interval under which this
        plugin should execute.
        """

    def get_name(self):
        """A simple name for this plugin."""
        return self.__module__ + ":" + self.__class__.__name__
