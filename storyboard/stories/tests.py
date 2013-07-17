"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
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
