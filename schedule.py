import sys
import os
import os.path
import unicodedata
from jadate import JaDate
from datetime import timedelta

TODAY = JaDate.today()

PRIORITY_RANGE = range(-20,20)
PRIORITY_LOW_RANGE = range(6, 20)
PRIORITY_NORMAL_RANGE = range(-5, 6)
PRIORITY_HIGH_RANGE = range(-15, -5)
PRIORITY_EXTREME_RANGE = range(-20, -15)

# スケジュールファイルの、1行分のレコードを保持する
class Schedule:
    def __init__(self, *data):
        self.done, self.date, self.priority, self.todo = data

    # ファイルから読んだ1行から、Scheduleを生成
    @classmethod
    def from_record(cls, line):
        done, date, priority, todo = line.rstrip().split(' ', 3)
        done = bool(int(done))
        date = JaDate.from_str(date, TODAY)
        priority = int(priority)
        return cls(done, date, priority, todo)

    # 日付、優先度、用事を指定して、Scheduleを生成
    # 各項目は、入力された文字列をそのまま渡す
    PRIORITY_TABLE = {'e':-18, 'h':-10, 'n':0, 'l':10}
    @classmethod
    def from_input(cls, date, priority, todo):
        if priority.lower() in Schedule.PRIORITY_TABLE:
            p = Schedule.PRIORITY_TABLE[priority]
        else:
            p = int(priority)

        if p not in PRIORITY_RANGE:
            msg = ('priority p must be ' + str(PRIORITY_RANGE.start) +
                   ' <= p < ' + str(PRIORITY_RANGE.stop) +
                   ', but ' + str(p) + ' given')
            raise ValueError(msg)

        return cls(False, JaDate.from_str(date, TODAY), p, todo)

    # 直接ファイルに書き出せる形式
    def __str__(self):
        done = str(int(self.done))
        date = self.date.format('{year:04}{month:02}{day:02}')
        prior = str(self.priority)
        return ' '.join([done, date, prior, self.todo])

    def fields(self):
        date = self.date.format('{year}/{month:02}/{day:02}({weekday})')
        return (date, str(self.priority), self.todo)

    # 過去の予定に関しては、Trueを返す
    def is_urgent(self):
        day = lambda d: timedelta(days=d)
        if self.priority in PRIORITY_EXTREME_RANGE:
            return True
        elif self.priority in PRIORITY_HIGH_RANGE:
            return self.date - TODAY <= day(30)
        elif self.priority in PRIORITY_NORMAL_RANGE:
            return self.date - TODAY <= day(7)
        elif self.priority in PRIORITY_LOW_RANGE:
            return self.date - TODAY <= day(3)
        else:
            assert False, "Program Error"

def read_schedule_file(filename):
    if not os.path.exists(filename):
        return []

    with open(filename) as f:
        schedules = [Schedule.from_record(line) for line in f if line]
    return schedules


"""
ファイルの上書きの際は、終了シグナルをtrapするより、
renameのアトミック性を利用した方がいい(man rename参照)

ファイル書き込みの旧実装:
    handlers = ignoreExitSignals()
    f = open(DATAFILENAME, 'w')
    # write on f
    f.close()
    restoreExitSignalHandlers(handlers)
これだと、writeの間中シグナルを受け付けなくなる
一旦一時ファイルに書き出して、renameする方がいい
だが、inode番号が変わるため、ハードリンクがある場合は使えない

def ignoreExitSignals():
    import signal
    signals = [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]
    handlerDictionary = {}
    for s in signals:
        handlerDictionary[s] = signal.getsignal(s)
        signal.signal(s, SIG_IGN)
    return handlerDictionary

def restoreExitSignalHandlers(handlerDictionary):
    import signal
    for sig in handlerDictionary:
        signal.signal(sig, handlerDictionary[sig])
"""
def write_to_schedule_file(schedule_list, filename):
    tmp = '__tmpfile__'
    with open(tmp, 'w') as f:
        for s in schedule_list:
            print(s, file=f)
    os.replace(tmp, filename)

# Scheduleのリストから、リストを表示するために必要なフィールドのリストを作る
# 例えば、以下の予定リストがあったとする。
#   [ Schedule: (2014/08/01(金), 0, アニメ上映会),
#     Schedule: (2014/08/04(月), 0, 飲み会),
#     Schedule: (2014/08/07(木), -18, 課題提出) ]
# 8月3日にschを実行し、addサブコマンドにより、以下の予定を加える。
#   Schedule: (2014/08/05(火), -10, 講演会)
# この時、make_fields_table関数により、以下のリストを得たい。
#   [ ('', '2014/08/04(月)', '0', '飲み会'),
#     ('*', '2014/08/05(月)', '-10', '講演会'),
#     ('', '2014/08/07(木)', '-18', '課題提出') ]
# filterとして、8月1日の予定を弾く関数を渡し、
# fields_getterとして、Scheduleを文字列の4-タプルに変換する関数を渡せば良い
def make_field_table(schedules, filter, fields_getter):
    return [fields_getter(s) for s in schedules if filter(s)]

def make_filter(filters, whitelist):
    return lambda s: all(f(s) for f in filters) or s in whitelist

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

def print_fields(field_table, print_headline=True):
    if print_headline:
        print(TODAY.format('*** {year}年{month}月{day}日　{weekday}曜日 ***'))

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
