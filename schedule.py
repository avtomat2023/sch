import sys
import os
import unicodedata
from jadate import JaDate
from datetime import timedelta

PRIORITY_RANGE = range(-20,20)
PRIORITY_LOW_RANGE = range(6, 20)
PRIORITY_NORMAL_RANGE = range(-5, 6)
PRIORITY_HIGH_RANGE = (-15, -5)
PRIORITY_EXTREME_RANGE = (-20, -15)

PRIORITY_LOW = 10
PRIORITY_NORMAL = 0
PRIORITY_HIGH = -10
PRIORITY_EXTREME = -18

# スケジュールファイルの、1行分のレコードを保持する
# レコードがどのような形式か指定する責任は、Scheduleが持つ
class Schedule:
    def __init__(self, *data):
        self.done, self.date, self.priority, self.todo = data

    # ファイルから読んだ1行から、Scheduleを生成
    @classmethod
    def from_record(cls, line):
        done, date, priority, todo = line.rstrip().split(' ', 3)
        done = bool(int(done))
        date = JaDate.from_str(date)
        priority = int(priority)
        return cls(done, date, priority, todo)

    # 日付(JaDate)、優先度(int)、用事(str)を指定して、Scheduleを生成
    @classmethod
    def from_data(cls, date, priority, todo):
        return cls(False, date, priority, todo)

    def fields(self):
        date = self.date.format('{year}/{month:02}/{day:02}({weekday})')
        return [date, str(self.priority), self.todo]

    # 過去の予定に関しては、Trueを返す
    def is_urgent(self):
        today = JaDate.today()
        day = lambda d: timedelta(days=d)
        if self.priority in PRIORITY_EXTREME_RANGE:
            return True
        elif self.priority in PRIORITY_HIGH_RANGE:
            return self.date - today <= day(30)
        elif self.priority in PRIORITY_NORMAL_RANGE:
            return self.date - today <= day(7)
        elif self.priority in PRIORITY_LOW_RANGE:
            return self.date - today <= day(3)
        else:
            assert False, "Program Error"

def read_schedule_file(filename):
    schedules = []
    with open(filename) as f:
        schedules = [Schedule.from_record(line) for line in f if line]
    return schedules

# Scheduleのリストから、リストを表示するために必要なフィールドのリストを作る
# 例えば、以下の予定リストがあったとする。
#   [ Schedule: (2014/08/01(金), 0, アニメ上映会),
#     Schedule: (2014/08/04(月), 0, 飲み会),
#     Schedule: (2014/08/07(木), -18, 課題提出) ]
# 8月3日にschを実行し、addサブコマンドにより、以下の予定を加える。
#   Schedule: (2014/08/05(火), -10, 講演会)
# この時、make_fields_table関数により、以下のリストを得たい。
#   [ ('', '2014/08/04(月)', '0', '飲み会'),
#     ('a', '2014/08/05(月)', '-10', '講演会'),
#     ('', '2014/08/07(木)', '-18', '課題提出') ]
# filterとして、8月1日の予定を弾く関数を渡し、
# fields_getterとして、Scheduleを文字列の4-タプルに変換する関数を渡せば良い
def make_field_table(schedules, filter, fields_getter):
    return [fields_getter(s) for s in schedules if filter(s)]

# charの端末上での文字幅を返す
def charwidth(char):
    # 私の環境では、Full-widthもAmbiguousもNot East Asianも
    # 半角文字として扱われていた
    if unicodedata.east_asian_width(char) == 'W':
        return 2
    else:
        return 1

def strwidth(s):
    return sum(charwidth(c) for c in s)

def print_fields(field_table):
    today = JaDate.today()
    print(today.format('{year}年{month}月{day}日　{weekday}曜日'))

    if not field_table:
        print('予定はありません')
        return

    nfield = len(field_table[0])
    header = tuple([''] * (nfield-3) + ['予定日', 'NICE', '用事'])
    field_table.insert(0, header)
    widths = [max(strwidth(s) for s in fields)
              for fields in zip(*field_table)]

    for fields in field_table:
        for field, width in zip(fields, widths):
            s = field + ' ' * (width - strwidth(field))
            print(s, end=' ')
        print()

"""
    # upcomingとoutdatedをソートし、scheduleIDsを更新する
    def _rehashSchedules(self):
        self.outdated.sort(key = lambda s: s.date)
        self.upcoming.sort(key = lambda s: s.date)
        self.scheduleIDs = {}
        i, iDone = -1, -1
        for s in reversed(self.outdated):
            if s.done:
                self.scheduleIDs[s] = 'd'+str(iDone)
                iDone -= 1
            else:
                self.scheduleIDs[s] = str(i)
                i -= 1
        i, iDone = 0, 0
        for s in self.upcoming:
            if s.isUrgent():
                if s.done:
                    self.scheduleIDs[s] = 'd'+str(iDone)
                    iDone += 1
                else:
                    self.scheduleIDs[s] = str(i)
                    i += 1
        for s in self.upcoming:
            if not s.isUrgent():
                if s.done:
                    self.scheduleIDs[s] = 'd'+str(iDone)
                    iDone += 1
                else:
                    self.scheduleIDs[s] = str(i)
                    i += 1
        self._isHashed = True

    def print(self, isHumanReadable, doesShowAll, doesShowDone):
        if not self._isHashed:
            self._rehashSchedules()

        toNotify = self._selectSchedulesToNotify(doesShowAll, doesShowDone)
        if isHumanReadable:
            self._notifyHumanReadable(toNotify)
        else:
            self._notifyInNormalForm(toNotify)

    def _selectSchedulesToNotify(self, doesShowAll, doesShowDone):
        toNotify = []
        for s in self.upcoming:
            if not s.done or doesShowDone:
                if doesShowAll:
                    toNotify.append(s)
                else:
                    if s.isUrgent():
                        toNotify.append(s)
        return toNotify

    def _notifyInNormalForm(self, notifyList):
        for s in notifyList:
            print('[' + self.scheduleIDs[s] + '] ', end='')
            print(s)

    def _notifyHumanReadable(self, notifyList):
        today = JaDate.today()
        print("%s %s" % (today, today.jaWeekday()+"曜日"))

        if len(notifyList) > 0:
            maxIDLen = max(len(self.scheduleIDs[s]) for s in notifyList)
            print(' ' * (maxIDLen+3), end='')
            print(Schedule.headline())
            for s in notifyList:
                print('[' + self.scheduleIDs[s] + '] ', end='')
                print(s.prettyStr())
        else:
            print("予定はありません。")

    def add(self, givenArgs):
        date = JaDate.fromStr(givenArgs[0])
        priority = int(givenArgs[1])
        todo = givenArgs[2]
        newSchedule = Schedule.fromData(date, priority, todo)

        today = JaDate.today()
        if newSchedule.date >= today:
            self.upcoming.append(newSchedule)
        else:
            self.outdated.append(newSchedule)
        self._isHashed = False

    def edit(self, givenArgs):
        self._isHashed = False

    def done(self, scheduleID):
        for s, sid in self.scheduleIDs.items():
            if sid == scheduleID:
                s.done = 1
                self._isHashed = False
                break
        else:
            print(scheduleID + "に対応するスケジュールが見つかりません。",
                  file=sys.stderr)

    def write(self, filename):
        if not self._isHashed:
            self._rehashSchedules()

        # UNIX系OSの場合は、renameとremoveの仕様上、うまくいく
        # （たぶんPOSIXのレベルで保証される）
        # Windowsではエラーになる
        # filenameがリンクだとまずいことになる
        tmpfilename = '/tmp/sch-tmpfile.' + str(os.getpid())
        f = open(tmpfilename, 'w')
        for s in self.outdated:
            print(s.done, s, file=f)
        for s in self.upcoming:
            print(s.done, s, file=f)
        os.rename(tmpfilename, filename)
        f.close()
"""
