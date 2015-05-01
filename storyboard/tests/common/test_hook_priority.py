# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

from oslo_config import cfg

import storyboard.common.hook_priorities as priority
import storyboard.tests.base as base

CONF = cfg.CONF


class TestHookPriority(base.TestCase):
    def test_hook_order(self):
        """Assert that the hook priorities are ordered properly."""

        self.assertLess(priority.PRE_AUTH, priority.AUTH)
        self.assertLess(priority.PRE_AUTH, priority.VALIDATION)
        self.assertLess(priority.PRE_AUTH, priority.POST_VALIDATION)
        self.assertLess(priority.PRE_AUTH, priority.DEFAULT)

        self.assertLess(priority.AUTH, priority.VALIDATION)
        self.assertLess(priority.AUTH, priority.POST_VALIDATION)
        self.assertLess(priority.AUTH, priority.DEFAULT)

        self.assertLess(priority.VALIDATION, priority.POST_VALIDATION)
        self.assertLess(priority.VALIDATION, priority.DEFAULT)

        self.assertLess(priority.POST_VALIDATION, priority.DEFAULT)
