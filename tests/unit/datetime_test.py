import unittest
import mock

from xd.docker.datetime import *


class tests(unittest.case.TestCase):

    def test_strptime_empty(self):
        dt = strptime('')
        self.assertIsNone(dt)

    def test_strptime_none(self):
        dt = strptime(None)
        self.assertIsNone(dt)

    def test_strptime_dummy_string(self):
        dt = strptime('0001-01-01T00:00:00Z')
        self.assertIsNone(dt)

    def test_strptime_1(self):
        dt = strptime('2015-10-19T20:33:42.123456')
        self.assertEqual(dt.year, 2015)
        self.assertEqual(dt.month, 10)
        self.assertEqual(dt.day, 19)
        self.assertEqual(dt.hour, 20)
        self.assertEqual(dt.minute, 33)
        self.assertEqual(dt.second, 42)
        self.assertEqual(dt.microsecond, 123456)

    def test_strptime_2(self):
        dt = strptime('1975-05-13T07:21:17.056789')
        self.assertEqual(dt.year, 1975)
        self.assertEqual(dt.month, 5)
        self.assertEqual(dt.day, 13)
        self.assertEqual(dt.hour, 7)
        self.assertEqual(dt.minute, 21)
        self.assertEqual(dt.second, 17)
        self.assertEqual(dt.microsecond, 56789)
