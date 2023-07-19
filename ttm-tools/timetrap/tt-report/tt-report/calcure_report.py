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

calcure_events_file = importlib.import_module("tt-report.lib.calcure_events_file")
CalcureEventsFile = calcure_events_file.CalcureEventsFile

BLOCK_MINS = 20

class CalcureReportType(Enum):
    BY_ETYPE = auto()
    BY_GCODE = auto()
    BY_ETYPE_AND_GCODE = auto()


class CalcureReportError(Exception):
    pass

class CalcureReport:
    def __init__(self, events_filename: str):
        self.calcure_events_file = CalcureEventsFile(events_filename)

    @classmethod
    def within_date(cls, start_date, event, days=7):
        event_date = datetime.datetime(int(event.year), int(event.month), int(event.day))
        end_date = start_date + datetime.timedelta(days=days)
        # print(event_date, start_date, end_date, days, event_date >= start_date and event_date < end_date)
        return event_date >= start_date and event_date < end_date

    @classmethod
    def datetime_s(cls, date):
        return date.strftime('%Y-%m-%d %a')

    @classmethod
    def interval_min(cls, interval_s):
        if len(interval_s) != 4:
            raise CalcureReportError(f'Expected interval to be of format HHMM: {interval_s}')
        hh = interval_s[:2]
        mm = interval_s[2:]

        return int(hh) * 60 + int(mm)
    
    def compute_week_calcure_report(self, week_start_date, only_remaining: bool, only_done: bool):
        datetime_s = self.datetime_s
        
        # filter events by date window
        events = self.calcure_events_file.events \
                 | pipe.where(lambda e: self.within_date(week_start_date, e, days=7)) \
                 | as_list
        
        if only_remaining:
            # filter out events that are finished already
            events = events | pipe.where(lambda e: e.priority.strip() != 'unimportant') | as_list
        elif only_done:
            events = events | pipe.where(lambda e: e.priority.strip() == 'unimportant') | as_list
            
        result = {}
        result['WEEK'] = {}
        result['WEEK']['WSUM'] = {}

        # compute sums for report type by each day
        for day in range(7):
            day_date = week_start_date + datetime.timedelta(days=day)

            # get the events just for this day
            day_events = events \
                    | pipe.where(lambda e: self.within_date(day_date, e, days=1)) \
                    | as_list
            
            # group by gcode for the day
            gcodes = list(day_events | pipe.map(lambda e: e.gcode) | pipe.Pipe(set))
            etags = list(day_events | pipe.map(lambda e: e.tag) | pipe.Pipe(set))
            result[datetime_s(day_date)] = {}
            result[datetime_s(day_date)]['DSUM'] = {}
            for gcode in gcodes:
                gcode_events = day_events | pipe.where(lambda e: e.gcode == gcode) | as_list

                result[datetime_s(day_date)][gcode] = {}
                for etag in etags:
                    gcode_etag_events = gcode_events | pipe.where(lambda e: e.tag == etag) | as_list
                    #interval_sum = sum(gcode_etag_events | pipe.map(lambda e: self.interval_min(e.end)) | as_list) / BLOCK_MINS
                    interval_sum = sum(gcode_etag_events | pipe.map(lambda e: self.interval_min(e.end)) | as_list)
                    if interval_sum == 0:
                        continue

                    result[datetime_s(day_date)][gcode][etag] = interval_sum
                    
                    if etag not in result[datetime_s(day_date)]['DSUM']:
                        result[datetime_s(day_date)]['DSUM'][etag] = 0
                    result[datetime_s(day_date)]['DSUM'][etag] += interval_sum

                    # compute sums for report in total per week
                    if gcode not in result['WEEK']:
                        result['WEEK'][gcode] = {}
                    if etag not in result['WEEK'][gcode]:
                        result['WEEK'][gcode][etag] = 0
                    if etag not in result['WEEK']['WSUM']:
                        result['WEEK']['WSUM'][etag] = 0

                    result['WEEK'][gcode][etag] += interval_sum
                    result['WEEK']['WSUM'][etag] += interval_sum

        return result

    def combine_etag_intervals(self, week_start_date, week_calcure_report: dict, skipped_etags=[]):

        def combine_etag_for_gcode(etag_intervals_for_gcode, is_week=False):
            etags = list(etag_intervals_for_gcode.keys())

            # Some tags should just be skipped and are documentation only. 
            # The MISSED events/tasks: MTSK, MEVT
            skipped_etags = ['MTSK', 'MEVT']

            # Get these separately, and if they're more than the commited tags, use them instead
            # Ignore WTSK and WEVT for any day and only max it for WEEK.
            max_etags = ['DTSK', 'DEVT', 'WTSK', 'WEVT']

            # get the sum of all commited events 
            commited_interval = sum(etags | pipe.where(lambda etag: etag not in skipped_etags and etag not in max_etags)
                                          | pipe.map(lambda etag: etag_intervals_for_gcode[etag])
                                          | as_list)

            max_etags_used = ['DTSK', 'DEVT'] if not is_week else ['WTSK', 'WEVT']

            # get the value that could be used if the interval is lower
            planned_interval = sum(etags | pipe.where(lambda etag: etag in max_etags_used)
                                         | pipe.map(lambda etag: etag_intervals_for_gcode[etag])
                                         | as_list)

            # return max(commited_interval, planned_interval)

            # for now, don't take these into account
            return commited_interval



        for day in range(7):
            day_date = week_start_date + datetime.timedelta(days=day)

            for gcode in week_calcure_report[self.datetime_s(day_date)].keys():
                week_calcure_report[self.datetime_s(day_date)][gcode] = \
                    combine_etag_for_gcode(week_calcure_report[self.datetime_s(day_date)][gcode],
                                           is_week=False)


        for gcode in week_calcure_report['WEEK'].keys():
            week_calcure_report['WEEK'][gcode] = \
                combine_etag_for_gcode(week_calcure_report['WEEK'][gcode],
                                        is_week=True)


        return week_calcure_report

    def convert_interval_format_for_calcure_report(self, week_calcure_report, keep_etags: bool):
        def process_interval(interval):
            #return interval / BLOCK_MINS
            #return int(interval / 60 * 100) / 100
            return f'{interval // 60:02}:{interval % 60:02}'



        if keep_etags:
            for date_key in week_calcure_report.keys():
                for gcode_key in week_calcure_report[date_key].keys():
                    for etag_key in week_calcure_report[date_key][gcode_key].keys():
                        week_calcure_report[date_key][gcode_key][etag_key] = process_interval(week_calcure_report[date_key][gcode_key][etag_key])
        else:
            for date_key in week_calcure_report.keys():
                for gcode_key in week_calcure_report[date_key].keys():
                    week_calcure_report[date_key][gcode_key] = process_interval(week_calcure_report[date_key][gcode_key])

        return week_calcure_report

    
    def create_week_calcure_report(self, week_start_date, keep_etags: bool, only_remaining: bool,
                                   only_done: bool):
        # Get a report for each day, each gcode, broken down by the event tag, and wweekly sum
        week_calcure_report = self.compute_week_calcure_report(week_start_date, 
                                                               only_remaining=only_remaining,
                                                               only_done=only_done)

        # the tag interval breakdown has some rules. such as MAX(DAY_EXPECTED, COMMITED)
        if not keep_etags:
            week_calcure_report = self.combine_etag_intervals(week_start_date, week_calcure_report)

        week_calcure_report = self.convert_interval_format_for_calcure_report(week_calcure_report, keep_etags)

        return json.dumps(week_calcure_report)



def main(args: argparse.Namespace):
    calcure_report = CalcureReport(args.events_file_path)
    week_start_date = datetime.datetime.strptime(args.week_start_date, '%Y-%m-%d')

    print(calcure_report.create_week_calcure_report(week_start_date, keep_etags=args.keep_etags,
                                                    only_remaining=args.remaining,
                                                    only_done=args.done))

# ==================================================================================================
def define_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument('events_file_path',                   
                   help="Events csv file path")
    p.add_argument('week_start_date',                   
                   help="The week start date to get the report for. %Y-%m-%d format expected.")

    p.add_argument('-k', '--keep_etags', action='store_true',
                   help="Do not sum per etags")
    p.add_argument('-r', '--remaining', action='store_true',
                   help="Only account for events not marked as done, or low priority in calcure ")
    p.add_argument('-d', '--done', action='store_true',
                   help="Only account for events marked as done, or low priority in calcure ")
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
                   
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

    main(define_args())

# ==================================================================================================
import unittest
class UnitTests(common.CommonTestCase):
    def test_dummy(self):
        self.assertEqual("dummy" != 0)

if __name__ == '__main__':
    _main()

