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

import abc
import six

from oslo_config import cfg
from stevedore.enabled import EnabledExtensionManager


CONF = cfg.CONF


def is_enabled(ext):
    """Check to see whether a plugin should be enabled. Assumes that the
    plugin extends PluginBase.

    :param ext: The extension instance to check.
    :return: True if it should be enabled. Otherwise false.
    """
    return ext.obj.enabled()


@six.add_metaclass(abc.ABCMeta)
class PluginBase(object):
    """Base class for all storyboard plugins.

    Every storyboard plugin will be provided an instance of the application
    configuration, and will then be asked whether it should be enabled. Each
    plugin should decide, given the configuration and the environment,
    whether it has the necessary resources to operate properly.
    """

    def __init__(self, config):
        self.config = config

    @abc.abstractmethod
    def enabled(self):
        """A method which indicates whether this plugin is properly
        configured and should be enabled. If it's ready to go, return True.
        Otherwise, return False.
        """


class StoryboardPluginLoader(EnabledExtensionManager):
    """The storyboard plugin loader, a stevedore abstraction that formalizes
    our plugin contract.
    """

    def __init__(self, namespace, on_load_failure_callback=None):
        super(StoryboardPluginLoader, self) \
            .__init__(namespace=namespace,
                      check_func=is_enabled,
                      invoke_on_load=True,
                      invoke_args=(CONF,),
                      on_load_failure_callback=on_load_failure_callback)
