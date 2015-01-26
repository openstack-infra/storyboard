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
import calendar
import datetime
import os
import pytz
import six

from oslo_log import log

from storyboard.common.working_dir import get_plugin_directory
import storyboard.plugin.base as plugin_base


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class CronPluginBase(plugin_base.PluginBase):
    """Base class for a plugin that executes business logic on a time
    interval. In order to prevent processing overlap on long-running
    processes that may exceed the tick interval, the plugin will be provided
    with the time range for which it is responsible.

    It is likely that multiple instances of a plugin may be running
    simultaneously, as a previous execution may not have finished processing
    by the time the next one is started. Please ensure that your plugin
    operates in a time bounded, thread safe manner.
    """

    @abc.abstractmethod
    def run(self, start_time, end_time):
        """Execute a periodic task.

        :param start_time: The last time the plugin was run.
        :param end_time: The current timestamp.
        :return: Nothing.
        """

    def _get_file_mtime(self, path, date=None):
        """Retrieve the date of this plugin's last_run file. If a date is
        provided, it will also update the file's date before returning that
        date.

        :param path: The path of the file to retreive.
        :param date: A datetime to use to set as the mtime of the file.
        :return: The mtime of the file.
        """

        # Get our timezones.
        utc_tz = pytz.utc

        # If the file doesn't exist, create it with a sane base time.
        if not os.path.exists(path):
            base_time = datetime.datetime \
                .utcfromtimestamp(0) \
                .replace(tzinfo=utc_tz)
            with open(path, 'a'):
                base_timestamp = calendar.timegm(base_time.timetuple())
                os.utime(path, (base_timestamp, base_timestamp))

        # If a date was passed, use it to update the file.
        if date:
            # If the date does not have a timezone, throw an exception.
            # That's bad practice and makes our date/time conversions
            # impossible.
            if not date.tzinfo:
                raise TypeError("Please include a timezone when passing"
                                " datetime instances")

            with open(path, 'a'):
                mtimestamp = calendar.timegm(date
                                             .astimezone(utc_tz)
                                             .timetuple())
                os.utime(path, (mtimestamp, mtimestamp))

        # Retrieve the file's last mtime.
        pid_info = os.stat(path)
        return datetime.datetime \
            .fromtimestamp(pid_info.st_mtime, utc_tz)

    def execute(self):
        """Execute this cron plugin, first by determining its own working
        directory, then calculating the appropriate runtime interval,
        and finally executing the run() method. If the working directory is
        not available, it will log an error and exit cleanly.
        """

        plugin_name = self.get_name()
        try:
            cron_directory = get_plugin_directory('cron')
        except IOError as e:
            LOG.error('Cannot create cron run cache: %s' % (e,))
            return

        lr_file = os.path.join(cron_directory, plugin_name)

        now = pytz.utc.localize(datetime.datetime.utcnow())

        start_time = self._get_file_mtime(path=lr_file)
        end_time = self._get_file_mtime(path=lr_file,
                                        date=now)
        self.run(start_time, end_time)

    @abc.abstractmethod
    def interval(self):
        """The plugin's cron interval, as a string.

        :return: The cron interval. Example: "* * * * *"
        """

    def get_name(self):
        """A simple name for this plugin."""
        return self.__module__ + ":" + self.__class__.__name__
