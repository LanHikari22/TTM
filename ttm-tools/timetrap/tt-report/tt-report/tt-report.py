#!/usr/bin/env python3
"""
This is a custom formatter script for timetrap. Use the JSON formatter and pipe it to this
"""
from curses.ascii import isdigit
import sys
import argparse
from typing import Dict, List, Optional, Callable, Any
from result import Ok, Err, Result
import json
import datetime
import calendar
from enum import Enum, auto
import pipe

import importlib  
common = importlib.import_module("tt-report.lib.common")
as_list = common.as_list

class LogEntry:
    def __init__(self, json_item):
        _id = json_item['id']
        _id = "%3d" % _id
        note = json_item['note']
        start_s = json_item['start']
        end_s = json_item['end']

        # parse the date and time out of start_s and end_s
        start_day = start_s.split(' ')[0]
        end_day = end_s.split(' ')[0]
        start = start_s.split(' ')[1]
        end = end_s.split(' ')[1]
        tstart = datetime.datetime.strptime(start, '%H:%M:%S')
        tend = datetime.datetime.strptime(end, '%H:%M:%S')

        # figure out week day from date
        date_dt = datetime.datetime.strptime(start_day, '%Y-%m-%d')
        week_day = calendar.day_name[date_dt.weekday()]
        date = '{0} {1}'.format(start_day, week_day[0:3])

        # round start and end to 5 minute interval
        tstart = tstart - datetime.timedelta(minutes=tstart.minute % 5, seconds=tstart.second,
                                             microseconds=tstart.microsecond)
        tend = tend - datetime.timedelta(minutes=tend.minute % 5, seconds=tend.second,
                                         microseconds=tend.microsecond)

        # figure out duration
        dt = datetime.timedelta(days=tend.day, hours=tend.hour, minutes=tend.minute)
        dt = dt - datetime.timedelta(days=tstart.day, hours=tstart.hour, minutes=tstart.minute)

        start = tstart.strftime('%H:%M')
        end = tend.strftime('%H:%M')
        dt_s = dur_to_hhmm(dt)

        # calculated state
        self.id: str = _id              # id of the entry, space padded by 3
        self.note: str = note           # note of entry
        self.week_day = week_day        # which day of the week. Ex: 'Monday'
        self.date_dt = date_dt          # The date of the entry in datetime type
        self.date = date                # Ex: '2022-01-06 Thu'
        self.tstart = tstart            # Start time, rounded to 5-minutes as date
        self.tend = tend                # End time, rounded to 5-minutes as date
        self.start = start              # start time in "%H:%M" format
        self.end = end                  # end time in "%H:%M" format
        self.dt = dt                    # duration (rounded computation) as timedelta
        self.dt_s = dt_s                # duration in "%H:%M" format

class WeekDayDisplaySetting(Enum):
    SingleChar = auto()
    TripleChar = auto()
    Full = auto()

    @staticmethod
    def parse(s: str) -> 'WeekDay.DisplaySetting':
        """
        s must be a number 0 (full), 1 (1 char), or 3 (3 char).
        :raises ValueError: if input is not parsable.
        """
        v = int(s)
        
        if v == 0:
            return WeekDay.DisplaySetting.Full
        if v == 1:
            return WeekDay.DisplaySetting.SingleChar
        if v == 3:
            return WeekDay.DisplaySetting.TripleChar

        raise ValueError(f'Failed to parse value {v}. Must be 0 (full), 1, or 3.')

class WeekDay(Enum):
    Mon = auto()
    Tue = auto()
    Wed = auto()
    Thu = auto()
    Fri = auto()
    Sat = auto()
    Sun = auto()

    def display(self, setting: 'WeekDayDisplaySetting'):
        weekdays = list(WeekDay.mro()[0])

        if setting == WeekDayDisplaySetting.SingleChar:
            displayed = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
        elif setting == WeekDayDisplaySetting.TripleChar:
            displayed = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        else: # setting == WeekCode.DisplaySetting.Full
            displayed = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return displayed[weekdays.index(self)]


    @staticmethod
    def parse(s: str) -> 'WeekDay':
        """
        :raises ValueError: if input is not parsable.
        """
        s = s.upper()
        if s in ['M', 'MON', 'MONDAY']:
            return WeekDay.Mon
        if s in ['T', 'TUE', 'TUESDAY']:
            return WeekDay.Tue
        if s in ['W', 'WED', 'WEDNESDAY']:
            return WeekDay.Wed
        if s in ['R', 'THU', 'THURSDAY']:
            return WeekDay.Thu
        if s in ['F', 'FRI', 'FRIDAY']:
            return WeekDay.Fri
        if s in ['S', 'SAT', 'SATURDAY']:
            return WeekDay.Sat
        if s in ['U', 'SUN', 'SUNDAY']:
            return WeekDay.Sun

        raise ValueError(f'Failed to parse string as WeekCode: {s}')
    


# ==================================================================================================
def dur_to_hhmm(dur: datetime.timedelta) -> str:
    """converts a duration to HH:MM format taking into account days (>24 hours in HH)"""
    hours = int(dur.seconds / 3600)
    minutes = int(dur.seconds / 60 % 60)
    # print('dur', dur, 'seconds', dur.seconds, 'hours', hours, 'minutes', minutes)

    return f'{hours:02}:{minutes:02}'


def sum_duration(entries: List[LogEntry]) -> Optional[datetime.timedelta]:
    res = None
    for entry in entries:
        if res is None:
            res = entry.dt
        else:
            # print('0', res, '+', entry.dt, '=', res + entry.dt)
            res = res + entry.dt
    
    return res


def sum_group_durations(entry_groups: Dict[Any, List[LogEntry]]) -> Optional[datetime.timedelta]:
    res = None
    for group in entry_groups:
        tot_dur = sum_duration(entry_groups[group])
        if tot_dur is not None:
            if res is None:
                res = tot_dur
            else:
                # print('1', res, '+', tot_dur, '=', res + tot_dur)
                res = res + tot_dur
    return res


def map_by_project(entry: LogEntry) -> Any:
    if entry.note.startswith('p(') and ')' in entry.note:
        project = entry.note[:entry.note.index(')')+1]
        return project
    return ''


def is_uuid(word: str) -> bool:
    if len(word) != 8:
        return False
    if not all([xi in '0123456789ABCDEF' for xi in word.upper()]):
        return False
    return True


def map_by_uuid(entry: LogEntry) -> Any:
    for token in entry.note.split(' '):
        if is_uuid(token):
            return token
    return ''


def map_by_parent_uuid(entry: LogEntry) -> Any:
    self_uuid = ''
    for token in entry.note.split(' '):
        if is_uuid(token):
            self_uuid = token

        if '.' in token:
            puuid = token.split('.')[0]
            if is_uuid(puuid):
                return puuid
    return self_uuid


def is_gcode(word: str) -> bool:
    gcode = word
    mcode = None
    if '-' in word:
        tokens = word.split('-')
        if len(tokens) != 2:
            return False

        gcode = tokens[0]
        mcode = tokens[1]

    if len(gcode) != 4:
        return False

    if gcode | pipe.map(lambda c: c.isdigit()) | as_list != [False, False, False, True]:
        return False

    if mcode != None:
        if mcode | pipe.map(lambda c: c.isdigit()) | as_list != [True, True, True, True]:
            return False

    return True


def map_by_gcode(entry: LogEntry) -> Any:
    for token in entry.note.split(' '):
        if is_gcode(token):
            return token
    return ''


def format_default(jsn) -> str:
    space_to_dur = len('408 2022-01-05 Wed 13:00 - 13:05 ') * ' '
    res = ''
    tot_dur_sum = None

    # group items by day
    dic = {}
    for item in jsn:
        entry = LogEntry(item)

        if entry.date not in dic:
            dic[entry.date] = [entry]
        else:
            dic[entry.date].append(entry)

    for day in dic:
        for entry in dic[day]:
            res += f'{entry.id} {entry.date} {entry.start} - {entry.end} {entry.dt_s} {entry.note}\n'

        dur_sum = sum_duration(dic[day])
        dur_sum_s = dur_to_hhmm(dur_sum)

        res += f'{space_to_dur}{dur_sum_s}\n'
        
    # print the duration for all entries
    tot_dur_sum = sum_group_durations(dic)
    if tot_dur_sum is not None:
        tot_dur_sum_s = dur_to_hhmm(tot_dur_sum)
        res += '-' * (len(space_to_dur) + len('00:00')) + '\n'
        res += f'{space_to_dur}{tot_dur_sum_s}\n'

    return res.strip()


def format_group_by_item_and_day(jsn, item_map: Callable[[LogEntry], Any]) -> str:
    """groups daily items together and sums their duration then tabs the individual logs for them"""
    now = datetime.datetime.now()
    sample_date_str = now.strftime(args.datefmt)
    # sample_date_str = '2022-01-05 Wed'

    space_to_dur = len(f'408 {sample_date_str} 13:00 - 13:05 ') * ' '
    len_date_weekday = len(sample_date_str)
    align_dur_dashes = '-' * (len('    ') + len(space_to_dur) - len_date_weekday)
    res = ''

    # map items by day by provided grouping
    dic = {}
    for item in jsn:
        entry = LogEntry(item)

        if entry.date not in dic:
            dic[entry.date] = {}

        if item_map(entry) not in dic[entry.date]:
            dic[entry.date][item_map(entry)] = [entry]
        else:
            dic[entry.date][item_map(entry)].append(entry)
        
    for day in dic:
        # sort groups by latest id
        groups = dic[day]
        groups = sorted(groups, key=lambda g: dic[day][g][-1].id)
        # date = dic[day][list(dic[day].keys())[0]][0].date
        date_dt = dic[day][list(dic[day].keys())[0]][0].date_dt
        date_str = date_dt.strftime(args.datefmt)

        for group in groups:
            dur = sum_duration(dic[day][group])
            dur_s = dur_to_hhmm(dur)

            res += f'{date_str}{align_dur_dashes}{dur_s} {group}\n'
            for entry in dic[day][group]:
                entry_date = entry.date_dt.strftime(args.datefmt)
                if group != entry.note:
                    res += f'    {entry.id} {entry_date} {entry.start} - {entry.end} {entry.dt_s}     {entry.note}\n'
                else:
                    res += f'    {entry.id} {entry_date} {entry.start} - {entry.end} {entry.dt_s}\n'
                pass

        # display day total
        tot_dur_sum = sum_group_durations(dic[day])
        if tot_dur_sum is not None:
            date_dashes = '-' * len_date_weekday
            note_dashes = '-' * 20
            res += f'{date_str}{align_dur_dashes}{dur_to_hhmm(tot_dur_sum)} {note_dashes}\n\n'


    return res.strip()


def format_group_by_item_and_week(jsn, item_map: Callable[[LogEntry], Any]) -> str:
    """groups weekly items together and sums their duration then tabs the individual logs for them"""
    space_to_dur = len('408 2022-01-05 Wed 13:00 - 13:05 ') * ' '
    len_date_weekday = len('2022-01-05 Week')
    align_dur_dashes = '-' * (len('    ') + len(space_to_dur) - len_date_weekday)
    res = ''

    # map items by week by provided grouping
    dic = {}
    for item in jsn:
        entry = LogEntry(item)

        week_date = entry.date_dt - datetime.timedelta(days=entry.date_dt.weekday())
        if week_date not in dic:
            dic[week_date] = {}

        if item_map(entry) not in dic[week_date]:
            dic[week_date][item_map(entry)] = [entry]
        else:
            dic[week_date][item_map(entry)].append(entry)
        
    for week in dic:
        # sort groups by latest id
        groups = dic[week]
        groups = sorted(groups, key=lambda g: dic[week][g][-1].id)

        week_date_s = f'{week.strftime(args.datefmt)} Week'
        for group in groups:
            dur = sum_duration(dic[week][group])
            dur_s = dur_to_hhmm(dur)

            res += f'{week_date_s}{align_dur_dashes}{dur_s} {group}\n'
            for entry in dic[week][group]:
                entry_date = entry.date_dt.strftime(args.datefmt)
                if group != entry.note:
                    res += f'    {entry.id} {entry_date} {entry.start} - {entry.end} {entry.dt_s}    {entry.note}\n'
                else:
                    res += f'    {entry.id} {entry_date} {entry.start} - {entry.end} {entry.dt_s}\n'

        # display day total
        tot_dur_sum = sum_group_durations(dic[week])
        if tot_dur_sum is not None:
            date_dashes = '-' * len_date_weekday
            note_dashes = '-' * 20
            res += f'{week_date_s}{align_dur_dashes}{dur_to_hhmm(tot_dur_sum)} {note_dashes}\n\n'

    return res.strip()


def main(args: argparse.Namespace):
    json_data = sys.stdin.read()
    jsn = json.loads(json_data)

    if args.format == 'default':
        print(format_default(jsn))

    if args.format == 'day-note':
        print(format_group_by_item_and_day(jsn, lambda e: e.note))
    if args.format == 'week-note':
        print(format_group_by_item_and_week(jsn, lambda e: e.note))

    if args.format == 'day-proj':
        print(format_group_by_item_and_day(jsn, map_by_project))
    if args.format == 'week-proj':
        print(format_group_by_item_and_week(jsn, map_by_project))

    if args.format == 'day-uuid':
        print(format_group_by_item_and_day(jsn, map_by_uuid))
    if args.format == 'week-uuid':
        print(format_group_by_item_and_week(jsn, map_by_uuid))

    if args.format == 'day-puuid':
        print(format_group_by_item_and_day(jsn, map_by_parent_uuid))
    if args.format == 'week-puuid':
        print(format_group_by_item_and_week(jsn, map_by_parent_uuid))

    if args.format == 'day-gcode':
        print(format_group_by_item_and_day(jsn, map_by_gcode))
    if args.format == 'week-gcode':
        print(format_group_by_item_and_week(jsn, map_by_gcode))

    # print(json.dumps(jsn, indent=4))

# ==================================================================================================
def define_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument('-f', '--format',
                   default='default',
                   nargs='?',
                   choices=['default', 
                            'day-note', 'day-proj', 'day-uuid', 'day-puuid', 'day-gcode',
                            'week-note', 'week-proj', 'week-uuid', 'week-puuid', 'week-gcode'],
                   help="choice from: ")
    p.add_argument("--datefmt",
                   default='%Y-%m-%d',
                   help="Format to display date as. Follows ISO-8601 standards.")
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
    # p.add_argument("--startday", type=WeekDay.parse,
    #                default=WeekDay.Mon,
    #                help="Day considered as beginning of week.")
    # p.add_argument("--daysetting", type=WeekDayDisplaySetting.parse,
    #                default=WeekDayDisplaySetting.SingleChar,
    #                help="How the day is displayed")
    # p.add_argument("--shortrelativedate", action='store_true',
    #                help="Sets the date to be relative to the start day in a compact form." + 
    #                     " Ex: 221121M")

    #  p.add_argument("required_int", type=int,
                   #  help="req number")
    #  p.add_argument("--on", action="store_true",
                   #  help="include to enable")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = False # True: must select a subcommand!

    sp = subparsers.add_parser('unittest', help='run the unit tests instead of main')

    return(p.parse_args())

def _main():
    if sys.version_info<(3,5,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        exit(1)
        
    # if you have unittest as part of the script, you can forward to it this way
    if len(sys.argv) >= 2 and sys.argv[1] == 'unittest':
        import unittest
        sys.argv[0] += ' unittest'
        sys.argv.remove('unittest')
        print(sys.argv)
        unittest.main()
        exit(0)
    if len(sys.argv) >= 1 and 'unittest' in sys.argv[0]:
        import unittest
        unittest.main()

    global args
    args = define_args()

    main(args)

# ==================================================================================================
import unittest
class UnitTests(common.CommonTestCase):
    def test_find_last_time(self):
        self.assertEqual(find_last_time('00:00:00 - 00:00:01 - 00:00:02 - beep'), '00:00:02')
        self.assertEqual(find_last_time('This has no time'), None)

if __name__ == '__main__':
    _main()
