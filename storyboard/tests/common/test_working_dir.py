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

from oslo.config import cfg

import storyboard.common.working_dir as working_dir
import storyboard.tests.base as base


CONF = cfg.CONF


class TestWorkingDir(base.TestCase):
    def setUp(self):
        super(TestWorkingDir, self).setUp()

        CONF.working_directory = os.tempnam()

        self.path = os.path.realpath(CONF.working_directory)

        self.addCleanup(self.cleanUp)

    def cleanUp(self):
        shutil.rmtree(self.path)
        working_dir.WORKING_DIRECTORY = None

    def test_get_working_directory(self):
        self.assertFalse(os.path.exists(self.path))

        working_dir_path = working_dir.get_working_directory()

        self.assertEqual(self.path, working_dir_path)
        self.assertTrue(os.path.exists(self.path))
        self.assertTrue(os.access(self.path, os.W_OK))

    def test_get_plugin_directory(self):
        plugin_name = 'my_test_plugin'
        plugin_path = os.path.join(self.path, 'plugin', plugin_name)

        self.assertFalse(os.path.exists(self.path))
        self.assertFalse(os.path.exists(plugin_path))

        resolved_path = working_dir.get_plugin_directory(plugin_name)

        self.assertEqual(plugin_path, resolved_path)
        self.assertTrue(os.path.exists(self.path))
        self.assertTrue(os.path.exists(plugin_path))

        self.assertTrue(os.access(self.path, os.W_OK))
        self.assertTrue(os.access(plugin_path, os.W_OK))
