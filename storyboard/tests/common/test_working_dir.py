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
import shutil
import stat

from oslo_config import cfg

import storyboard.common.working_dir as working_dir
import storyboard.tests.base as base


CONF = cfg.CONF

PERM_READ_ONLY = stat.S_IRUSR + stat.S_IRGRP + stat.S_IROTH
PERM_ALL = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO


class TestWorkingDir(base.TestCase):
    def test_get_working_directory(self):
        '''Assert that the get_working_directory() method makes use of the
        configured path if it has the permissions to manage it.
        '''
        # Set a temporary directory
        CONF.set_override('working_directory', os.path.realpath(os.tempnam()))
        self.assertFalse(os.path.exists(CONF.working_directory))

        working_dir_path = working_dir.get_working_directory()

        self.assertEqual(CONF.working_directory, working_dir_path)
        self.assertTrue(os.path.exists(CONF.working_directory))
        self.assertTrue(os.access(CONF.working_directory, os.W_OK))

        # Clean up after ourselves.
        shutil.rmtree(CONF.working_directory)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None

    def test_working_directory_not_creatable(self):
        """Assert that the get_working_directory() method raises an error if
        it cannot be created.
        """
        read_only = stat.S_IRUSR + stat.S_IRGRP + stat.S_IROTH
        all_permissions = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO

        # Create a temporary directory
        temp_base = os.tempnam()
        os.makedirs(temp_base)
        os.chmod(temp_base, read_only)

        temp_path = "%s/temp_file" % (temp_base,)

        # Set a temporary directory
        CONF.set_override('working_directory', temp_path)
        self.assertFalse(os.path.exists(CONF.working_directory))

        # Make sure it raises an exception.
        self.assertRaises(IOError, working_dir.get_working_directory)

        os.chmod(temp_base, all_permissions)

        # Clean up after ourselves.
        shutil.rmtree(temp_base)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None

    def test_working_directory_not_writable(self):
        """Assert that the get_working_directory() method raises an error if
        it cannot be created.
        """

        # Create a temporary directory
        temp_path = os.tempnam()
        os.makedirs(temp_path)
        os.chmod(temp_path, PERM_READ_ONLY)

        # Set a temporary directory
        CONF.set_override('working_directory', temp_path)
        self.assertTrue(os.path.exists(CONF.working_directory))

        # Make sure it raises an exception.
        self.assertRaises(IOError, working_dir.get_working_directory)

        os.chmod(temp_path, PERM_ALL)

        # Clean up after ourselves.
        shutil.rmtree(temp_path)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None

    def test_working_directory_is_file(self):
        """Assert that the get_working_directory() method raises an error if
        it cannot be created.
        """

        # Create a temporary directory and a file.
        temp_base = os.tempnam()
        os.makedirs(temp_base)
        temp_path = "%s/temp_file" % (temp_base,)
        open(temp_path, 'a').close()

        # Configure the temp_path to the created file.
        CONF.set_override('working_directory', temp_path)
        self.assertTrue(os.path.exists(CONF.working_directory))

        # Make sure it raises an exception.
        self.assertRaises(IOError, working_dir.get_working_directory)

        # Clean up after ourselves.
        shutil.rmtree(temp_base)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None

    def test_get_plugin_directory(self):
        temp_path = os.path.realpath(os.tempnam())
        CONF.set_override('working_directory', temp_path)

        plugin_name = 'my_test_plugin'
        plugin_path = os.path.join(CONF.working_directory, 'plugin',
                                   plugin_name)

        self.assertFalse(os.path.exists(CONF.working_directory))
        self.assertFalse(os.path.exists(plugin_path))

        resolved_path = working_dir.get_plugin_directory(plugin_name)

        self.assertEqual(plugin_path, resolved_path)
        self.assertTrue(os.path.exists(CONF.working_directory))
        self.assertTrue(os.path.exists(plugin_path))

        self.assertTrue(os.access(CONF.working_directory, os.W_OK))
        self.assertTrue(os.access(plugin_path, os.W_OK))

        shutil.rmtree(temp_path)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None

    def test_get_plugin_directory_parent_locked(self):
        temp_path = os.path.realpath(os.tempnam())
        CONF.set_override('working_directory', temp_path)

        # Create the directory and lock it down.
        working_dir.get_working_directory()
        self.assertTrue(os.path.exists(CONF.working_directory))
        os.chmod(CONF.working_directory, PERM_READ_ONLY)

        plugin_name = 'my_test_plugin'
        plugin_path = os.path.join(CONF.working_directory, 'plugin',
                                   plugin_name)
        self.assertFalse(os.path.exists(plugin_path))

        self.assertRaises(IOError,
                          working_dir.get_plugin_directory, plugin_name)

        # Reset permissions and clean up
        os.chmod(CONF.working_directory, PERM_ALL)

        shutil.rmtree(CONF.working_directory)
        CONF.clear_override('working_directory')
        working_dir.WORKING_DIRECTORY = None
