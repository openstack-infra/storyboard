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

import atexit

from oslo_log import log

from oslo.config import cfg
from storyboard.plugin.base import StoryboardPluginLoader
from storyboard.plugin.cron.manager import CronManager


LOG = log.getLogger(__name__)
CONF = cfg.CONF

CRON_OPTS = [
    cfg.StrOpt("plugin",
               default="storyboard.plugin.cron.manager:CronManager",
               help="The name of the cron plugin to execute.")
]


def main():
    """Run a specific cron plugin from the commandline. Used by the system's
    crontab to target different plugins on different execution intervals.
    """
    CONF.register_cli_opts(CRON_OPTS)
    log.register_options(CONF)
    CONF(project='storyboard')
    log.setup(CONF, 'storyboard')

    loader = StoryboardPluginLoader(namespace="storyboard.plugin.cron")

    if loader.extensions:
        loader.map(execute_plugin, CONF.plugin)


def execute_plugin(ext, name):
    """Private handler method that checks individual loaded plugins.
    """
    plugin_name = ext.obj.get_name()
    if name == plugin_name:
        LOG.info("Executing cron plugin: %s" % (plugin_name,))
        ext.obj.execute()


def load_crontab():
    """Initialize all registered crontab plugins."""

    # We cheat here - crontab plugin management is implemented as a crontab
    # plugin itself, so we create a single instance to kick things off,
    # which will then add itself to recheck periodically.
    manager_plugin = CronManager(CONF)
    if manager_plugin.enabled():
        manager_plugin.execute()
        atexit.register(unload_crontab, manager_plugin)
    else:
        unload_crontab(manager_plugin)


def unload_crontab(manager_plugin):
    manager_plugin.remove()
