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

from apscheduler.triggers.interval import IntervalTrigger
from oslo_config import cfg
from stevedore.extension import Extension

from storyboard.plugin.base import StoryboardPluginLoader
import storyboard.plugin.scheduler as scheduler
import storyboard.tests.base as base
from storyboard.tests.plugin.scheduler.mock_plugin import MockPlugin


CONF = cfg.CONF


class TestSchedulerCoreMethods(base.DbTestCase):
    """Test methods defined in __init__.py."""

    def setUp(self):
        super(TestSchedulerCoreMethods, self).setUp()
        self.addCleanup(self._remove_scheduler)

    def _remove_scheduler(self):
        if scheduler.SCHEDULER:
            scheduler.shutdown_scheduler()

    def test_disabled_initialize(self):
        """Test that the initialize method does nothing when disabled."""
        CONF.set_override('enable', False, 'scheduler')

        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.initialize_scheduler()
        self.assertIsNone(scheduler.SCHEDULER)

        CONF.clear_override('enable', 'scheduler')

    def test_enabled_initialize(self):
        """Test that the initialize and shutdown methods work when enabled."""
        CONF.set_override('enable', True, 'scheduler')

        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.initialize_scheduler()
        self.assertIsNotNone(scheduler.SCHEDULER)
        scheduler.shutdown_scheduler()
        self.assertIsNone(scheduler.SCHEDULER)

        CONF.clear_override('enable', 'scheduler')

    def test_intialize_with_manager(self):
        """Assert that the management plugin is loaded, and runs every
        minute.
        """
        CONF.set_override('enable', True, 'scheduler')

        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.initialize_scheduler()
        self.assertIsNotNone(scheduler.SCHEDULER)

        manager_job = scheduler.SCHEDULER \
            .get_job(scheduler.SCHEDULE_MANAGER_ID)

        self.assertIsNotNone(manager_job)
        trigger = manager_job.trigger
        self.assertIsInstance(trigger, IntervalTrigger)
        self.assertEqual(60, trigger.interval_length)
        self.assertEqual(scheduler.SCHEDULE_MANAGER_ID, manager_job.id)

        scheduler.shutdown_scheduler()
        self.assertIsNone(scheduler.SCHEDULER)

        CONF.clear_override('enable', 'scheduler')

    def test_add_new_not_safe(self):
        """Try to add a plugin to a nonexistent scheduler."""

        # Make sure that invoking without a scheduler is safe.
        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.add_plugins(dict())
        self.assertIsNone(scheduler.SCHEDULER)

    def test_add_new(self):
        """Add a new plugin to the scheduler."""
        CONF.set_override('enable', True, 'scheduler')

        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.initialize_scheduler()

        mock_plugin = MockPlugin(dict())
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [
            Extension(mock_plugin_name, None, None, mock_plugin)
        ]
        loader = StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )
        test_list = list()
        loader.map(scheduler.add_plugins, test_list)

        self.assertTrue(test_list.index(mock_plugin_name) == 0)

        self.assertIsNotNone(scheduler.SCHEDULER.get_job(mock_plugin_name))

        scheduler.shutdown_scheduler()
        self.assertIsNone(scheduler.SCHEDULER)
        CONF.clear_override('enable', 'scheduler')

    def test_add_plugins_reschedule(self):
        """Assert that the test_add_plugins will reschedule existing plugins.
        """
        CONF.set_override('enable', True, 'scheduler')

        self.assertIsNone(scheduler.SCHEDULER)
        scheduler.initialize_scheduler()

        mock_plugin = MockPlugin(dict())
        mock_plugin_name = mock_plugin.get_name()
        mock_extensions = [
            Extension(mock_plugin_name, None, None, mock_plugin)
        ]
        loader = StoryboardPluginLoader.make_test_instance(
            mock_extensions, namespace='storyboard.plugin.testing'
        )
        test_list = list()
        loader.map(scheduler.add_plugins, test_list)

        self.assertTrue(test_list.index(mock_plugin_name) == 0)
        first_run_job = scheduler.SCHEDULER.get_job(mock_plugin_name)
        first_run_trigger = first_run_job.trigger
        self.assertEqual(mock_plugin._trigger.run_date,
                         first_run_trigger.run_date)

        # Update the plugin's interval and re-run
        new_date = datetime.datetime.now() + datetime.timedelta(days=2)
        mock_plugin._trigger = DateTrigger(run_date=new_date)
        test_list = list()
        loader.map(scheduler.add_plugins, test_list)

        # make sure the plugin is only loaded once.
        self.assertTrue(test_list.index(mock_plugin_name) == 0)
        self.assertEqual(len(test_list), 1)

        # Get the job.
        second_run_job = scheduler.SCHEDULER.get_job(mock_plugin_name)
        second_run_trigger = second_run_job.trigger
        self.assertNotEqual(second_run_trigger.run_date,
                            first_run_trigger.run_date)

        scheduler.shutdown_scheduler()
        self.assertIsNone(scheduler.SCHEDULER)
        CONF.clear_override('enable', 'scheduler')
