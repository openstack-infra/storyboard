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

from stevedore.extension import Extension

import storyboard.plugin.base as plugin_base
import storyboard.tests.base as base


class TestPluginBase(base.TestCase):
    def setUp(self):
        super(TestPluginBase, self).setUp()

        self.extensions = []
        self.extensions.append(Extension(
            'test_one', None, None,
            TestBasePlugin(dict())
        ))

    def test_extensibility(self):
        """Assert that we can actually instantiate a plugin."""

        plugin = TestBasePlugin(dict())
        self.assertIsNotNone(plugin)
        self.assertTrue(plugin.enabled())

    def test_plugin_loader(self):
        manager = plugin_base.StoryboardPluginLoader.make_test_instance(
            self.extensions,
            namespace='storyboard.plugin.testing'
        )

        results = manager.map(self._count_invocations)

        # One must exist.
        self.assertEqual(1, len(manager.extensions))

        # One should be invoked.
        self.assertEqual(1, len(results))

    def _count_invocations(self, ext):
        return 1


class TestBasePlugin(plugin_base.PluginBase):
    def enabled(self):
        return True
