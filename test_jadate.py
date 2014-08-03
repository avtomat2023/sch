import datetime
from jadate import *
import unittest

class TestJaDate(unittest.TestCase):
    def setUp(self):
        self.today = JaDate(2014, 8, 3)

    def test8(self):
        d = JaDate.from_str('20140123', self.today)
        self.assertEqual(d.year, 2014)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 23)

    def test4ThisYear(self):
        d = JaDate.from_str('0804', self.today)
        self.assertEqual(d.year, 2014)
        self.assertEqual(d.month, 8)
        self.assertEqual(d.day, 4)

    def test4NextYear(self):
        d = JaDate.from_str('0802', self.today)
        self.assertEqual(d.year, 2015)
        self.assertEqual(d.month, 8)
        self.assertEqual(d.day, 2)

    def testFormat(self):
        date = JaDate(2014, 8, 3)
        s = date.format('{year}/{month:02}/{day:02}({weekday})')
        self.assertEqual(s, '2014/08/03(日)')

if __name__ == '__main__':
    unittest.main()
