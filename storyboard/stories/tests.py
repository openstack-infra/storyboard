# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

    def test_more_addition(self):
        """Tests that 2 + 1 always equals 3.
        """
        self.assertEqual(2 + 1, 3)

    def test_even_more_addtion(self):
        """Tests that 2 + 2 always equals 4.
        """
        self.assertEqual(2 + 2, 4)

    def test_yet_more_addition(self):
        """Tests that 3 + 2 always equals 5.
        """
        self.assertEqual(3 + 2, 5)
