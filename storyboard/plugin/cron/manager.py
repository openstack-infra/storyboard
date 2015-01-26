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

from crontab import CronTab
from oslo.config import cfg
from oslo_log import log

from storyboard.common.working_dir import get_working_directory
from storyboard.plugin.base import StoryboardPluginLoader
from storyboard.plugin.cron.base import CronPluginBase


LOG = log.getLogger(__name__)

CRON_MANAGEMENT_OPTS = [
    cfg.BoolOpt('enable',
                default=False,
                help='Enable StoryBoard\'s Crontab management.')
]
CONF = cfg.CONF
CONF.register_opts(CRON_MANAGEMENT_OPTS, 'cron')


class CronManager(CronPluginBase):
    """A Cron Plugin serves both as the manager for other storyboard
    cron tasks, and as an example plugin for storyboard. It checks every
    5 minutes or so to see what storyboard cron plugins are registered vs.
    running, and enables/disables them accordingly.
    """

    def __init__(self, config, tabfile=None):
        super(CronManager, self).__init__(config=config)

        self.tabfile = tabfile

    def enabled(self):
        """Indicate whether this plugin is enabled. This indicates whether
        this plugin alone is runnable, as opposed to the entire cron system.
        Note that this plugin cannot operate if the system cannot create a
        working directory.
        """
        try:
            # This will raise an exception if the working directory cannot
            # be created.
            get_working_directory()

            # Return the configured cron flag.
            return self.config.cron.enable
        except IOError as e:
            LOG.error("Cannot enable crontab management: Working directory is"
                      " not available: %s" % (e,))
            return False

    def interval(self):
        """This plugin executes every 5 minutes.

        :return: "*/5 * * * *"
        """
        return "*/5 * * * *"

    def run(self, start_time, end_time):
        """Execute a periodic task.

        :param start_time: The last time the plugin was run.
        :param end_time: The current timestamp.
        """

        # First, go through the stevedore registration and update the plugins
        # we know about.
        loader = StoryboardPluginLoader(namespace="storyboard.plugin.cron")
        handled_plugins = dict()
        if loader.extensions:
            loader.map(self._manage_plugins, handled_plugins)

        # Now manually go through the cron list and remove anything that
        # isn't registered.
        cron = CronTab(tabfile=self.tabfile)
        not_handled = lambda x: x.comment not in handled_plugins
        jobs = filter(not_handled, cron.find_command('storyboard-cron'))
        cron.remove(*jobs)
        cron.write()

    def _manage_plugins(self, ext, handled_plugins=dict()):
        """Adds a plugin instance to crontab."""
        plugin = ext.obj

        cron = CronTab(tabfile=self.tabfile)
        plugin_name = plugin.get_name()
        plugin_interval = plugin.interval()
        command = "storyboard-cron --plugin %s" % (plugin_name,)

        # Pull any existing jobs.
        job = None
        for item in cron.find_comment(plugin_name):
            LOG.info("Found existing cron job: %s" % (plugin_name,))
            job = item
            job.set_command(command)
            job.set_comment(plugin_name)
            job.setall(plugin_interval)
            break

        if not job:
            LOG.info("Adding cron job: %s" % (plugin_name,))
            job = cron.new(command=command, comment=plugin_name)
            job.setall(plugin_interval)

        # Update everything.
        job.set_command(command)
        job.set_comment(plugin_name)
        job.setall(plugin_interval)

        # This code us usually not triggered, because the stevedore plugin
        # loader harness already filters based on the results of the
        # enabled() method, however we're keeping it in here since plugin
        # loading and individual plugin functionality are independent, and may
        # change independently.
        if plugin.enabled():
            job.enable()
        else:
            LOG.info("Disabled cron plugin: %s", (plugin_name,))
            job.enable(False)

        # Remember the state of this plugin
        handled_plugins[plugin_name] = True

        # Save it.
        cron.write()

    def remove(self):
        """Remove all storyboard cron extensions.
        """
        # Flush all orphans
        cron = CronTab(tabfile=self.tabfile)
        cron.remove_all(command='storyboard-cron')
        cron.write()
