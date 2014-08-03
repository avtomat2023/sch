from schedule import *
import unittest

class TestSchedule(unittest.TestCase):
    def setUp(self):
        self.schedules = [
            Schedule.from_record('0 20140801 0 アニメ上映会\n'),
            Schedule.from_record('1 20140804 -10 CodeIQ提出期限\n'),
            Schedule.from_record('0 20140807 -18 アルゴリズム 課題提出\n'),
        ]

    def test_from_record(self):
        s = Schedule.from_record('0 20140807 -18 アルゴリズム 課題提出\n')
        self.assertFalse(s.done)
        self.assertEqual(s.date.year, 2014)
        self.assertEqual(s.date.month, 8)
        self.assertEqual(s.date.day, 7)
        self.assertEqual(s.priority, -18)
        self.assertEqual(s.todo, 'アルゴリズム 課題提出')

    def test_str(self):
        line = '0 20140807 -18 アルゴリズム 課題提出'
        s = Schedule.from_record(line + '\n')
        self.assertEqual(str(s), line)

    def test_fields(self):
        s = Schedule.from_record('0 20140807 -18 アルゴリズム 課題提出\n')
        fields = s.fields()
        date = '2014/08/07(木)'
        prior = '-18'
        todo = 'アルゴリズム 課題提出'
        self.assertEqual(fields, [date, prior, todo])

    def test_make_field_table(self):
        def filter(s):
            return s.date >= JaDate(2014, 8, 3)
        def fields(s):
            done = 'd' if s.done else ''
            return tuple([done] + s.fields())

        table1 = make_field_table(self.schedules, filter, fields)
        table2 = [
            ('d', '2014/08/04(月)', '-10', 'CodeIQ提出期限'),
            ('', '2014/08/07(木)', '-18', 'アルゴリズム 課題提出'),
        ]
        self.assertEqual(table1, table2)

    def test_strwidth(self):
        s = 'abcdeあいうえお'
        self.assertEqual(strwidth(s), 15)

if __name__ == '__main__':
    unittest.main()
