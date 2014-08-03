#!/usr/bin/env python3
import schedule
import sys
import os
import os.path
import bisect
from operator import methodcaller
from argparse import ArgumentParser

def filter_past(sch):
    return sch.date >= schedule.TODAY

def filter_low_priority(sch):
    return sch.is_urgent()

def filter_done(sch):
    return not sch.done

DATAFILENAME = os.path.join(os.path.dirname(__file__), 'schedule-list')

def show(schedule_list, args, filters):
    if args.show_done:
        def fields(s):
            if s.done:
                return ('d',) + s.fields()
            else:
                return ('',) + s.fields()
    else:
        def fields(s):
            return s.fields()
    filter = schedule.make_filter(filters, [])
    table = schedule.make_field_table(schedule_list, filter, fields)
    schedule.print_fields(table)

def add(schedule_list, args, filters):
    to_add = schedule.Schedule.from_input(args.date, args.priority, args.todo)
    keys = [s.date for s in schedule_list]
    i = bisect.bisect_right(keys, to_add.date)
    schedule_list.insert(i, to_add)
    schedule.write_to_schedule_file(schedule_list, DATAFILENAME)

    print('予定を追加しました。')
    filter = schedule.make_filter(filters, [to_add])
    def fields(s):
        if s is to_add:
            return ('*',) + s.fields()
        elif s.done:
            return ('d',) + s.fields()
        else:
            return ('',) + s.fields()
    table = schedule.make_field_table(schedule_list, filter, fields)
    schedule.print_fields(table)

def done(schedule_list, args, filters):
    select = [(i,s) for (i,s) in enumerate(schedule_list)
              if all(f(s) for f in filters) and not s.done]
    if not select:
        print('未実行の予定はありません。')
        return

    schedules = [s for (i,s) in select]
    numbers = {id(s):n for (n,(i,s)) in enumerate(select)}

    print('実行済みの予定を番号で選択してください。')
    print('複数選択する場合、半角スペースで区切ってください。')
    print()
    # 選択画面の数字を右揃えにする
    align = '{:>' + str(len(str(len(schedules)-1))) + '}:'
    def fields(s):
        return (align.format(numbers[id(s)]),) + s.fields()
    table = schedule.make_field_table(schedules, lambda x:True, fields)
    schedule.print_fields(table, False)
    print()

    done_nums = [int(s) for s in input('> ').split()
                 if int(s) in range(len(schedules))]
    for n in done_nums:
        schedules[n].done = True
    schedule.write_to_schedule_file(schedule_list, DATAFILENAME)

    print()
    print(str(len(done_nums)) + '個の予定を実行済みにしました。')
    filter = schedule.make_filter(filters, [schedules[n] for n in done_nums])
    def fields(s):
        if numbers.get(id(s)) in done_nums:
            return ('D',) + s.fields()
        elif s.done:
            return ('d',) + s.fields()
        else:
            return ('',) + s.fields()
    table = schedule.make_field_table(schedule_list, filter, fields)
    schedule.print_fields(table)

parser = ArgumentParser(description='コマンドラインベースTODOマネージャ',
                        add_help=False)

parser.add_argument(
    '-a', '--show-all', action='store_true',
    help='直近のものだけでなく、今後すべての予定を表示します'
)
parser.add_argument(
    '-d', '--show-done', action='store_true',
    help='実行済みの予定も表示します'
)
parser.add_argument(
    '-h', '--help', action='help',
    help='このヘルプメッセージを表示します'
)

subparsers = parser.add_subparsers()

"""
addコマンド使用例
sch a 20110520 e 微積分の中間試験
日付は以下の形式が利用できる
yyyymmdd : 年月日を指定
mmdd     : 本日以降の直近の月日を指定
mdd      : 本日以降の直近の月日を指定
優先度(NICE値)は直接数値で指定する他、以下の略記が使える
e:最優先(Extreme) h:高(High) n:通常(Normal) l:低(Low)
"""
parser_add = subparsers.add_parser(
    'add', aliases=['a'], add_help=False,
    help='指定された日付,優先度,用事の予定を追加します'
)
parser_add.add_argument(
    'date', action='store',
    help='日付（指定方法:20140803 0803 803）'
)
parser_add.add_argument(
    'priority', action='store',
    help='NICE値（e=-18, h=-10, n=0, l=10）'
)
parser_add.add_argument(
    'todo', action='store', help='用事'
)
parser_add.add_argument(
    '-h', '--help', action='help',
    help='このヘルプメッセージを表示します'
)
parser_add.set_defaults(subcommand=add)

parser_done = subparsers.add_parser(
    'done', aliases=['d'], add_help=False, help='実行済みの予定を選択します'
)
parser_done.set_defaults(subcommand=done)

if __name__ == '__main__':
    args = parser.parse_args()

    schedule_list = schedule.read_schedule_file(DATAFILENAME)

    filters = [filter_past]
    if not args.show_all:
        filters.append(filter_low_priority)
    if not args.show_done:
        filters.append(filter_done)

    if 'subcommand' in args:
        args.subcommand(schedule_list, args, filters)
    else:
        show(schedule_list, args, filters)
