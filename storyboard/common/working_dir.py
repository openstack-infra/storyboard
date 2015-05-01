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

import six

from oslo_config import cfg
from oslo_log import log


LOG = log.getLogger(__name__)

CONF = cfg.CONF
CONF.register_opts([
    cfg.StrOpt('working_directory',
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

        # Expand users, backlinks, and references.
        path = os.path.expanduser(CONF.working_directory)
        path = os.path.realpath(path)

        try:
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != 17:
                    # Not an already exists error
                    raise

            # Now that we know it exists, assert that it's a directory
            if not os.path.isdir(path):
                raise Exception("%s is not a directory." % (path,))

            # Make sure we can write to it.
            if not os.access(path, os.W_OK):
                raise Exception("%s is not writeable." % (path,))

        except (OSError, Exception) as e:
            # We're expecting OSError or Exception here. Recast and resend,
            # so that any part of the application can respond.
            message = six.text_type(e)
            LOG.error("Cannot create working directory: %s" % (message,))
            raise IOError(message)

        # Use this directory and return.
        WORKING_DIRECTORY = path

    return WORKING_DIRECTORY


def get_plugin_directory(plugin_name):
    """Resolve and create a working directory for a third party plugin.

    :param plugin_name: A unique plugin name.
    :return: The fully qualified path of the working directory.
    """
    directory = os.path.join(get_working_directory(), 'plugin', plugin_name)

    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except (OSError, Exception) as e:
            message = six.text_type(e)
            LOG.error("Cannot create plugin directory: %s" % (message,))
            raise IOError(message)

    return directory
