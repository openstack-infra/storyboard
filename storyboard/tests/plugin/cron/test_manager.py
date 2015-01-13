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


import os
import tempfile

import crontab
from oslo.config import cfg
from stevedore.extension import Extension

import storyboard.plugin.base as plugin_base
import storyboard.plugin.cron.manager as cronmanager
import storyboard.tests.base as base
from storyboard.tests.plugin.cron.mock_plugin import MockPlugin


CONF = cfg.CONF


class TestCronManager(base.TestCase):
    def setUp(self):
        super(TestCronManager, self).setUp()

        (user, self.tabfile) = tempfile.mkstemp(prefix='cron_')

        # Flush the crontab before test.
        cron = crontab.CronTab(tabfile=self.tabfile)
        cron.remove_all(command='storyboard-cron')
        cron.write()

        CONF.register_opts(cronmanager.CRON_MANAGEMENT_OPTS, 'cron')
        CONF.set_override('enable', True, group='cron')

    def tearDown(self):
        super(TestCronManager, self).tearDown()
        CONF.clear_override('enable', group='cron')

        # Flush the crontab after test.
        cron = crontab.CronTab(tabfile=self.tabfile)
        cron.remove_all(command='storyboard-cron')
        cron.write()

        os.remove(self.tabfile)

    def test_enabled(self):
        """This plugin must be enabled if the configuration tells it to be
        enabled.
        """
        enabled_plugin = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        self.assertTrue(enabled_plugin.enabled())

        CONF.set_override('enable', False, group='cron')
        enabled_plugin = cronmanager.CronManager(CONF)
        self.assertFalse(enabled_plugin.enabled())
        CONF.clear_override('enable', group='cron')

    def test_interval(self):
        """Assert that the cron manager runs every 5 minutes."""

        plugin = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        self.assertEqual("*/5 * * * *", plugin.interval())

    def test_manage_plugins(self):
        """Assert that the cron manager adds plugins to crontab."""

        mock_plugin = MockPlugin(dict())
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [Extension('test_one', None, None, mock_plugin)]

        loader = plugin_base.StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )

        # Run the add_plugin routine.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        loader.map(manager._manage_plugins)

        # Manually test the crontab.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronContains(
            command='storyboard-cron --plugin %s' % (mock_plugin_name,),
            comment=mock_plugin.get_name(),
            interval=mock_plugin.interval(),
            enabled=mock_plugin.enabled()
        )

    def test_manage_disabled_plugin(self):
        """Assert that a disabled plugin is added to the system crontab,
        but disabled. While we don't anticipate this feature to ever be
        triggered (since the plugin loader won't present disabled plugins),
        it's still a good safety net.
        """
        mock_plugin = MockPlugin(dict(), is_enabled=False)
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [Extension('test_one', None, None, mock_plugin)]

        loader = plugin_base.StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )

        # Run the add_plugin routine.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        loader.map(manager._manage_plugins)

        # Manually test the crontab.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronContains(
            command='storyboard-cron --plugin %s' % (mock_plugin_name,),
            comment=mock_plugin.get_name(),
            interval=mock_plugin.interval(),
            enabled=mock_plugin.enabled()
        )

    def test_manage_existing_update(self):
        """Assert that a plugin whose signature changes is appropriately
        updated in the system crontab.
        """
        mock_plugin = MockPlugin(dict(),
                                 plugin_interval="*/10 * * * *",
                                 is_enabled=False)
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [Extension('test_one', None, None, mock_plugin)]

        loader = plugin_base.StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )

        # Run the add_plugin routine.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        loader.map(manager._manage_plugins)

        # Manually test the crontab.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronContains(
            command='storyboard-cron --plugin %s' % (mock_plugin_name,),
            comment=mock_plugin.get_name(),
            interval=mock_plugin.interval(),
            enabled=mock_plugin.enabled()
        )

        # Update the plugin and re-run the loader
        mock_plugin.plugin_interval = "*/5 * * * *"
        loader.map(manager._manage_plugins)

        # re-test the crontab.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronContains(
            command='storyboard-cron --plugin %s' % (mock_plugin_name,),
            comment=mock_plugin.get_name(),
            interval=mock_plugin.interval(),
            enabled=mock_plugin.enabled()
        )

    def test_remove_plugin(self):
        """Assert that the remove() method on the manager removes plugins from
        the crontab.
        """
        mock_plugin = MockPlugin(dict(), is_enabled=False)
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [Extension('test_one', None, None, mock_plugin)]

        loader = plugin_base.StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )

        # Run the add_plugin routine.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        loader.map(manager._manage_plugins)

        # Manually test the crontab.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronContains(
            command='storyboard-cron --plugin %s' % (mock_plugin_name,),
            comment=mock_plugin.get_name(),
            interval=mock_plugin.interval(),
            enabled=mock_plugin.enabled()
        )

        # Now run the manager's remove method.
        manager.remove()

        # Make sure we don't leave anything behind.
        self.assertCronLength(0, command='storyboard-cron')

    def test_remove_only_storyboard(self):
        """Assert that the remove() method manager only removes storyboard
        plugins, and not others.
        """
        # Create a test job.
        cron = crontab.CronTab(tabfile=self.tabfile)
        job = cron.new(command='echo 1', comment='echo_test')
        job.setall("0 0 */10 * *")
        cron.write()

        # Create a plugin and have the manager add it to cron.
        mock_plugin = MockPlugin(dict(), is_enabled=False)
        mock_extensions = [Extension('test_one', None, None, mock_plugin)]

        loader = plugin_base.StoryboardPluginLoader.make_test_instance(
            mock_extensions,
            namespace='storyboard.plugin.testing'
        )
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        loader.map(manager._manage_plugins)

        # Assert that there's two jobs in our cron.
        self.assertCronLength(1, command='storyboard-cron')
        self.assertCronLength(1, comment='echo_test')

        # Call manager remove.
        manager.remove()

        # Check crontab.
        self.assertCronLength(0, command='storyboard-cron')
        self.assertCronLength(1, comment='echo_test')

        # Clean up after ourselves.
        cron = crontab.CronTab(tabfile=self.tabfile)
        cron.remove_all(comment='echo_test')
        cron.write()

    def test_remove_not_there(self):
        """Assert that the remove() method is idempotent and can happen if
        we're already unregistered.
        """
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager.remove()

    def test_execute(self):
        """Test that execute() method adds plugins."""

        # Actually run the real cronmanager.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager.execute()

        # We're expecting 2 in-branch plugins.
        self.assertCronLength(2, command='storyboard-cron')

    def test_execute_update(self):
        """Test that execute() method updates plugins."""

        # Manually create an instance of a known plugin with a time interval
        # that doesn't match what the plugin wants.
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager_name = manager.get_name()
        manager_command = "storyboard-cron --plugin %s" % (manager_name,)
        manager_comment = manager_name
        manager_old_interval = "0 0 */2 * *"

        cron = crontab.CronTab(tabfile=self.tabfile)
        job = cron.new(
            command=manager_command,
            comment=manager_comment
        )
        job.enable(False)
        job.setall(manager_old_interval)
        cron.write()

        # Run the manager
        manager.execute()

        # Check a new crontab to see what we find.
        self.assertCronLength(1, command=manager_command)

        cron = crontab.CronTab(tabfile=self.tabfile)
        for job in cron.find_command(manager_command):
            self.assertNotEqual(manager_old_interval, job.slices)
            self.assertEqual(manager.interval(), job.slices)
            self.assertTrue(job.enabled)

        # Cleanup after ourselves.
        manager.remove()

        # Assert that things are gone.
        self.assertCronLength(0, command='storyboard-cron')

    def test_execute_remove_orphans(self):
        """Test that execute() method removes orphaned/deregistered plugins."""

        # Manually create an instance of a plugin that's not in our default
        # stevedore registration
        plugin = MockPlugin(dict())
        plugin_name = plugin.get_name()
        plugin_command = "storyboard-cron --plugin %s" % (plugin_name,)
        plugin_comment = plugin_name
        plugin_interval = plugin.interval()

        cron = crontab.CronTab(tabfile=self.tabfile)
        job = cron.new(
            command=plugin_command,
            comment=plugin_comment
        )
        job.enable(False)
        job.setall(plugin_interval)
        cron.write()

        # Run the manager
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager.execute()

        # Check a new crontab to see what we find.
        self.assertCronLength(0, command=plugin_command)
        self.assertCronLength(2, command='storyboard-cron')

        # Cleanup after ourselves.
        manager.remove()

        # Assert that things are gone.
        self.assertCronLength(0, command='storyboard-cron')

    def test_execute_add_new(self):
        """Test that execute() method adds newly registered plugins."""

        # Manuall add the cron manager
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager_name = manager.get_name()
        manager_command = "storyboard-cron --plugin %s" % (manager_name,)
        manager_comment = manager_name

        cron = crontab.CronTab(tabfile=self.tabfile)
        job = cron.new(
            command=manager_command,
            comment=manager_comment
        )
        job.enable(manager.enabled())
        job.setall(manager.interval())
        cron.write()

        # Run the manager
        manager = cronmanager.CronManager(CONF, tabfile=self.tabfile)
        manager.execute()

        # Check a new crontab to see what we find.
        self.assertCronLength(2, command='storyboard-cron')

        # Cleanup after ourselves.
        manager.remove()

        # Assert that things are gone.
        self.assertCronLength(0, command='storyboard-cron')

    def assertCronLength(self, length=0, command=None, comment=None):
        cron = crontab.CronTab(tabfile=self.tabfile)
        if command:
            self.assertEqual(length,
                             len(list(cron.find_command(command))))
        elif comment:
            self.assertEqual(length,
                             len(list(cron.find_comment(comment))))
        else:
            self.assertEqual(0, length)

    def assertCronContains(self, command, comment, interval, enabled=True):
        cron = crontab.CronTab(tabfile=self.tabfile)
        found = False

        for job in cron.find_comment(comment):
            if job.command != command:
                continue
            elif job.comment != comment:
                continue
            elif job.enabled != enabled:
                continue
            elif str(job.slices) != interval:
                continue
            else:
                found = True
                break
        self.assertTrue(found)
