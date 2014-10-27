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
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from oslo.config import cfg

from storyboard.openstack.common import log

LOG = log.getLogger(__name__)

CONF = cfg.CONF
CONF.register_opts([
    cfg.ListOpt('working_directory',
                default='~/.storyboard',
                help='The root path to storyboard\'s working directory.')
])

WORKING_DIRECTORY = None


def get_working_directory():
    """Returns the path to our runtime working directory, making sure it exists
    if necessary.
    """
    global WORKING_DIRECTORY

    if not WORKING_DIRECTORY:
        # Try to resolve the configured directory.
        conf_path = os.path.realpath(CONF.working_directory)

        if not os.path.exists(conf_path):
            try:
                os.makedirs(conf_path)
            except Exception:
                # Hard exit, we need this.
                LOG.error("Cannot create working directory: %s" % (conf_path,))
                exit(1)

            if not os.path.isdir(conf_path):
                LOG.error("Configured working directory is not a directory: %s"
                          % (conf_path,))
                exit(1)

            if not os.access(conf_path, os.W_OK):
                LOG.error("Cannot write to working directory: %s"
                          % (conf_path,))
                exit(1)

            # We've passed all our checks, let's save our working directory.
            WORKING_DIRECTORY = conf_path

    return WORKING_DIRECTORY


def get_plugin_directory(plugin_name):
    """Resolve and create a working directory for a third party plugin.

    :param plugin_name: A unique plugin name.
    :return: The fully qualified path of the working directory.
    """
    directory = os.path.join(get_working_directory(), 'plugin', plugin_name)

    if not os.path.exists(directory):
        os.makedirs(directory)

    return directory
