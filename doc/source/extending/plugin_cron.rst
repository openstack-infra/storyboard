==================================
Extending StoryBoard: Cron Plugins
==================================

Overview
--------

StoryBoard requires the occasional periodic task, to support things like
cleanup and maintenance. It does this by directly managing its own crontab
entries, and extension hooks are available for you to add your own
functionality. Crontab entries are checked every 5 minutes,
with new entries added and old/orphaned entries removed. Note that this
monitoring is only active while the storyboard api is running. As soon as the
API is shut down, all cron plugins are shut down as well.

When your plugin is executed, it is done so via `storyboard-cron` which
bootstraps configuration and storyboard. It does not maintain state
between runs, and terminates as soon as your code finishes.

We DO NOT recommend you use this extension mechanism to create long running
processes. Upon the execution of your plugin's `run()` method,
you will be provided with the time it was last executed, as well as the current
timestamp. Please limit your plugin's execution scope to events that occurred
within that time frame, and exit after.

Cron Plugin Quickstart
----------------------

Step 1: Create a new python project using setuptools
####################################################

This is left as an exercise to the reader. Don't forget to include storyboard
as a requirement.

Step 2: Implement your plugin
#############################

Add a registered entry point in your plugin's `setup.cfg`. The name should be
reasonably unique::

    [entry_points]
    storyboard.plugin.cron =
         my-plugin-cron = my.namespace.plugin:CronWorker

Then, implement your plugin by extending `CronPluginBase`. You may register
your own configuration groups, please see
`oslo.config <https://docs.openstack.org/oslo.config/latest/reference/cfg.html>`_
for more details.::

    from storyboard.plugin.cron.base import CronPluginBase

    class MyCronPlugin(CronPluginBase):

        def enabled(self):
            '''This method should return whether the plugin is enabled and
            configured. It has access to self.config, which is a reference to
            storyboard's global configuration object.
            '''
            return True

        def interval(self):
            '''This method should return the crontab interval for this
            plugin's execution schedule. It is used verbatim.
            '''
            return "? * * * *"

        def run(self, start_time, end_time):
            '''Execute your plugin. The provided parameters are the start and
            end times of the time window for which this particular execution
            is responsible.

            This particular implementation simply deletes oauth tokens that
            are older than one week.
            '''

            lastweek = datetime.utcnow() - timedelta(weeks=1)

            query = api_base.model_query(AccessToken)
            query = query.filter(AccessToken.expires_at < lastweek)
            query.delete()


Step 3: Install your plugin
###########################
Finally, install your plugin, which may require you switch into storyboard's
virtual environment. Pip should  automatically register your plugin::

    pip install my-storyboard-plugin
