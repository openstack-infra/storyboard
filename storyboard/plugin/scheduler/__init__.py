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
import six

from oslo_config import cfg
from oslo_log import log
from pytz import utc

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.interval import IntervalTrigger

from storyboard.db.api.base import get_engine
from storyboard.plugin.base import StoryboardPluginLoader


LOG = log.getLogger(__name__)
CONF = cfg.CONF
SCHEDULER = None
SCHEDULE_MANAGER_ID = 'storyboard-scheduler-manager'

SCHEDULER_OPTS = [
    cfg.BoolOpt("enable",
                default=False,
                help="Whether to enable the scheduler.")
]
CONF.register_opts(SCHEDULER_OPTS, 'scheduler')


def initialize_scheduler():
    """Initialize the task scheduler. This method configures the global
    scheduler, checks the loaded tasks, and ensures they are all scheduled.
    """
    global SCHEDULER

    # If the scheduler is not enabled, clear it and exit. This prevents any
    # unexpected database session issues.
    if not CONF.scheduler.enable:
        if SCHEDULER:
            SCHEDULER.remove_all_jobs()
            SCHEDULER = None
        LOG.info("Scheduler is not enabled.")
        return

    # Use SQLAlchemy as a Job store.
    jobstores = {
        'default': SQLAlchemyJobStore(engine=get_engine())
    }

    # Two executors: The default is for all plugins. The second one is for
    # the scheduler manager, which makes sure this scheduler instance is
    # aware of all of our plugins.
    executors = {
        'default': ThreadPoolExecutor(10),
        'manager': ThreadPoolExecutor(1),
    }

    # Allow executions to coalesce. See https://apscheduler.readthedocs.org/en
    # /latest/userguide.html#missed-job-executions-and-coalescing
    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'replace_existing': True
    }

    # This will automatically create the table.
    SCHEDULER = BackgroundScheduler(jobstores=jobstores,
                                    executors=executors,
                                    job_defaults=job_defaults,
                                    timezone=utc)

    SCHEDULER.start()
    atexit.register(shutdown_scheduler)

    # Make sure we load in the update_scheduler job. If it exists,
    # we remove/update it to make sure any code changes get propagated.
    if SCHEDULER.get_job(SCHEDULE_MANAGER_ID):
        SCHEDULER.remove_job(SCHEDULE_MANAGER_ID)
    SCHEDULER.add_job(
        update_scheduler,
        id=SCHEDULE_MANAGER_ID,
        trigger=IntervalTrigger(minutes=1),
        executor='manager',
        replace_existing=True
    )


def shutdown_scheduler():
    """Shut down the scheduler. This method is registered using atexit,
    and is run whenever the process in which initialize_scheduler() was
    called ends.
    """
    global SCHEDULER

    if SCHEDULER:
        LOG.info("Shutting down scheduler")
        SCHEDULER.shutdown()
        SCHEDULER = None


def update_scheduler():
    """Update the jobs loaded into the scheduler. This runs every minute to
    keep track of anything that's since been loaded into our execution hooks.
    """
    global SCHEDULER
    if not SCHEDULER:
        LOG.warning("Scheduler does not exist, cannot update it.")
        return

    # Load all plugins that are registered and load them into the scheduler.
    loader = StoryboardPluginLoader(namespace="storyboard.plugin.scheduler")
    loaded_plugins = [SCHEDULE_MANAGER_ID]
    if loader.extensions:
        loader.map(add_plugins, loaded_plugins)

    # Now manually go through the list of jobs in the scheduler and remove
    # any that haven't been loaded, since some might have been uninstalled.
    for job in SCHEDULER.get_jobs():
        if job.id not in loaded_plugins:
            LOG.info('Removing Job: %s' % (job.id,))
            SCHEDULER.remove_job(job.id)


def add_plugins(ext, loaded_plugins=list()):
    global SCHEDULER
    if not SCHEDULER:
        LOG.warning('Scheduler does not exist')
        return

    # Extract the plugin instance
    plugin = ext.obj

    # Get the plugin name
    plugin_name = six.text_type(plugin.get_name())

    # Plugin trigger object.
    plugin_trigger = plugin.trigger()

    # Plugin personal activation logic. This is duplicated from
    # StoryboardPluginLoader, replicated here just in case that ever changes
    # without us knowing about it.
    plugin_enabled = plugin.enabled()

    # Check to see if we have one of these loaded...
    current_job = SCHEDULER.get_job(plugin_name)

    # Assert that the trigger is of the correct type.
    if not isinstance(plugin_trigger, BaseTrigger):
        LOG.warning("Plugin does not provide BaseTrigger: %s" % (plugin_name,))
        plugin_enabled = False

    # If the plugin should be disabled, disable it, then exist.
    if not plugin_enabled:
        if current_job:
            LOG.info("Disabling plugin: %s" % (plugin_name,))
            SCHEDULER.remove_job(plugin_name)
        return

    # At this point we know it's loaded.
    loaded_plugins.append(plugin_name)

    # If it's already registered, check for a
    if current_job:
        # Reschedule if necessary. We're using a string comparison here
        # because they're declarative for basic triggers, and because there's
        # no other real good option.
        if six.text_type(current_job.trigger) != six.text_type(plugin_trigger):
            LOG.info('Rescheduling Job: %s' % (plugin_name,))
            SCHEDULER.reschedule_job(plugin_name, trigger=plugin_trigger)
        return

    # At this point, load the plugin.
    LOG.info('Adding job: %s' % (plugin_name,))
    SCHEDULER.add_job(
        execute_plugin,
        args=[plugin.__class__],
        id=plugin_name,
        trigger=plugin_trigger,
        executor='default',
        replace_existing=True
    )


def execute_plugin(plugin_class):
    """Run a specific cron plugin from the scheduler."""

    plugin_instance = plugin_class(CONF)
    LOG.info('Running plugin: %s' % (plugin_instance.get_name(),))
    plugin_instance.run()

    # This line is here for testability.
    return plugin_instance
