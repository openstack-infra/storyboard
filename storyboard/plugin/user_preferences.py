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

from oslo_log import log
import six

from storyboard._i18n import _LE
from storyboard.plugin.base import PluginBase
from storyboard.plugin.base import StoryboardPluginLoader


LOG = log.getLogger(__name__)
PREFERENCE_DEFAULTS = dict()


def initialize_user_preferences():
    """Initialize any plugins that were installed via pip. This will parse
    out all the default preference values into one dictionary for later
    use in the API.
    """
    manager = StoryboardPluginLoader(
        namespace='storyboard.plugin.user_preferences')

    if manager.extensions:
        manager.map(load_preferences, PREFERENCE_DEFAULTS)


def load_preferences(ext, defaults):
    """Load all plugin default preferences into our cache.

    :param ext: The extension that's handling this event.
    :param defaults: The current dict of default preferences.
    """

    plugin_defaults = ext.obj.get_default_preferences()

    for key in plugin_defaults:
        if key in defaults:
            # Let's not error out here.
            LOG.error(_LE("Duplicate preference key %s found.") % (key,))
        else:
            defaults[key] = plugin_defaults[key]


@six.add_metaclass(abc.ABCMeta)
class UserPreferencesPluginBase(PluginBase):
    """Base class for a plugin that provides a set of expected user
    preferences and their default values. By extending this plugin, you can
    add preferences for your own storyboard plugins and workers, and have
    them be manageable via your web client (Your client may need to be
    customized).
    """

    @abc.abstractmethod
    def get_default_preferences(self):
        """Return a dictionary of preferences and their default values."""
