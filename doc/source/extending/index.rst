==============================
Extending StoryBoard: Overview
==============================

StoryBoard provides many extension points that allow you to customize its
functionality to your own needs. All of these are implemented using
`stevedore <http://stevedore.readthedocs.org>`_, so that installing them is
simple, straightforward, and independent of the storyboard core libraries.
StoryBoard itself makes use of these extension points,
providing several 'in-branch' plugins that you may use as a template for your
own work.

Getting Started
---------------

Registering your extensions
```````````````````````````

Stevedore uses setup entry point hooks to determine which plugins are
available. To begin, you should register your implementation classes in your
setup.cfg file. For example::

    [entry_points]
    storyboard.plugin.user_preferences =
         my-plugin-config = my.namespace.plugin:UserPreferences
    storyboard.plugin.worker =
         my-plugin-worker = my.namespace.plugin:EventWorker
    storyboard.plugin.cron =
         my-plugin-cron = my.namespace.plugin:CronWorker

Configuring and enabling your extensions
````````````````````````````````````````

Every plugin type builds on `storyboard.plugin.base:PluginBase`,
which supports your plugin's configuration. Upon creation,
storyboard's global configuration is injected into the plugin as the `config`
property. With this object, it is left to  the developer to implement the
`enabled()` method, which informs storyboard that it has all it needs to
operate.

An example basic plugin::

    class BasicPlugin(PluginBase):

        def enabled(self):
            return self.config.my_config_property

Each extension hook may also add its own requirements, which will be detailed
below.

Available Extension Points
--------------------------

User Preferences
````````````````

The simplest, and perhaps most important, extension point,
allows you to inject default preferences into storyboard. These will be made
available via the API for consumption by the webclient,
however you will need to consume those preferences yourself::

    [entry_points]
    storyboard.plugin.user_preferences =
         my-plugin-config = my.namespace.plugin:UserPreferences

To learn how to write a user preference plugin, please contribute to this
documentation.

Cron Workers
````````````

Frequently you will need to perform time-based, repeated actions within
storyboard, such as maintenance. By creating and installing a cron
plugin, StoryBoard will manage and maintain your crontab registration for you::

    [entry_points]
    storyboard.plugin.cron =
         my-plugin-cron = my.namespace.plugin:CronWorker

To learn how to write a cron plugin, `read more here <./plugin_cron.html>`_.

Event Workers
`````````````

If you would like your plugin to react to a specific API event in storyboard,
you can write a plugin to do so. This plugin will receive notification
whenever a POST, PUT, or DELETE action occurs on the API,
and your plugin can decide how to process each event in an asynchronous
thread which will not impact the stability of the API::

    [entry_points]
    storyboard.plugin.worker =
         my-plugin-worker = my.namespace.plugin:EventWorker

To learn how to write an event worker plugin, `read more here
<./plugin_worker.html>`_.
