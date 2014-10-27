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
import storyboard.plugin.user_preferences as prefs_base
import storyboard.tests.base as base


class TestUserPreferencesPluginBase(base.TestCase):
    def setUp(self):
        super(TestUserPreferencesPluginBase, self).setUp()

        self.extensions = []
        self.extensions.append(Extension(
            'test_one', None, None,
            TestPreferencesPlugin(dict())
        ))
        self.extensions.append(Extension(
            'test_two', None, None,
            TestOtherPreferencesPlugin(dict())
        ))

    def test_extensibility(self):
        """Assert that we can actually instantiate a plugin."""

        plugin = TestPreferencesPlugin(dict())
        self.assertIsNotNone(plugin)
        self.assertTrue(plugin.enabled())

    def test_plugin_loader(self):
        """Perform a single plugin loading run, including two plugins and a
        couple of overlapping preferences.
        """
        manager = plugin_base.StoryboardPluginLoader.make_test_instance(
            self.extensions,
            namespace='storyboard.plugin.user_preferences')

        loaded_prefs = dict()

        self.assertEqual(2, len(manager.extensions))
        manager.map(prefs_base.load_preferences, loaded_prefs)

        self.assertTrue("foo" in loaded_prefs)
        self.assertTrue("omg" in loaded_prefs)
        self.assertTrue("lol" in loaded_prefs)

        self.assertEqual(loaded_prefs["foo"], "baz")
        self.assertEqual(loaded_prefs["omg"], "wat")
        self.assertEqual(loaded_prefs["lol"], "cat")


class TestPreferencesPlugin(prefs_base.UserPreferencesPluginBase):
    def get_default_preferences(self):
        return {
            "foo": "baz",
            "omg": "wat"
        }

    def enabled(self):
        return True


class TestOtherPreferencesPlugin(prefs_base.UserPreferencesPluginBase):
    def get_default_preferences(self):
        return {
            "foo": "bar",
            "lol": "cat"
        }

    def enabled(self):
        return True
