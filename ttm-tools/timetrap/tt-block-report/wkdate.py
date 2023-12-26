import sys
import argparse
import datetime
import result
from result import Result, Ok, Err
from typing import Dict, Tuple, List
import unittest


def tryparseint(s) -> Result[int, None]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(())


class Seasons:
    def __init__(self):
        self.seasons = Seasons.get_seasons()

    @staticmethod
    def get_seasons() -> Dict[str, Tuple[int, int, int]]:
        '''
        recorded season dates according to Northern Hemisphere. 
        key: YYYY-S=Spring, YYYY-M=Summer, YYYY-F=Fall, YYYY-W=Winter
        val: tuple (Y, M, D)
        '''
        tup = Seasons.datetup_of
        off = lambda s: Seasons.dayoffset(s).unwrap()
        return {
            '2019-S': tup(datetime.date(2019, 3, 20) - datetime.timedelta(days=off('Wednesday'))),
            '2019-M': tup(datetime.date(2019, 6, 21) - datetime.timedelta(days=off('Friday'))),
            '2019-F': tup(datetime.date(2019, 9, 23) - datetime.timedelta(days=off('Monday'))),
            '2019-W': tup(datetime.date(2019, 12, 21) - datetime.timedelta(days=off('Saturday'))),

            '2020-S': tup(datetime.date(2020, 3, 19) - datetime.timedelta(days=off('Thursday'))),
            '2020-M': tup(datetime.date(2020, 6, 20) - datetime.timedelta(days=off('Saturday'))),
            '2020-F': tup(datetime.date(2020, 9, 22) - datetime.timedelta(days=off('Tuesday'))),
            '2020-W': tup(datetime.date(2020, 12, 21) - datetime.timedelta(days=off('Monday'))),

            '2021-S': tup(datetime.date(2021, 3, 20) - datetime.timedelta(days=off('Saturday'))),
            '2021-M': tup(datetime.date(2021, 6, 20) - datetime.timedelta(days=off('Sunday'))),
            '2021-F': tup(datetime.date(2021, 9, 22) - datetime.timedelta(days=off('Wednesday'))),
            '2021-W': tup(datetime.date(2021, 12, 21) - datetime.timedelta(days=off('Tuesday'))),

            '2022-S': tup(datetime.date(2022, 3, 20) - datetime.timedelta(days=off('Sunday'))),
            '2022-M': tup(datetime.date(2022, 6, 21) - datetime.timedelta(days=off('Tuesday'))),
            '2022-F': tup(datetime.date(2022, 9, 22) - datetime.timedelta(days=off('Thursday'))),
            '2022-W': tup(datetime.date(2022, 12, 21) - datetime.timedelta(days=off('Wednesday'))),
        }

    def season_of(self, datetup: Tuple[int, int, int]) -> Result[Tuple[str, Tuple[int, int, int]], str]:
        """
        returns the closest season to `date` or error
        """

        # find last match that is less than date
        match = ()
        for season_key in self.seasons:
            season_datetup = self.seasons[season_key]
            if datetime.date(*season_datetup).toordinal() < datetime.date(*datetup).toordinal():
                match = (season_key, season_datetup)

        if match == ():
            return Err('failed to get season for {}'.format(datetime.date(*datetup)))
        return Ok(match)

    def weekdate_of(self, date: datetime.date) -> str:
        seasons = Seasons()
        week = date.isocalendar()[1]

        which_season, season_datetup = seasons.season_of(
            Seasons.datetup_of(date)).unwrap()
        season_date = datetime.date(*season_datetup)
        season_week = season_date.isocalendar()[1]

        return 'Y{}{}-W{}{}'.format(
            which_season[2:4], which_season[-1],
            (week+1) - season_week,
            Seasons.to_shortday(date.strftime('%A')).unwrap()
        )

    def parse_weekdate(self, weekdate: str) -> Result[datetime.date, str]:
        bad_form_msg = 'Expected Y<YY>[SFMW]-W<week>[MTWRFSU]. Ex: Y21M-W13F'
        def err_bad_form(s): return Err(
            '\'{}\': bad form. {}'.format(s, bad_form_msg))

        if '-' not in weekdate or 'Y' not in weekdate or 'W' not in weekdate:
            return err_bad_form(weekdate)

        split = weekdate.split('-')
        if len(split) != 2:
            return err_bad_form(weekdate)

        year_s, week_s = split[0], split[1]
        if not year_s.startswith('Y') or len(year_s) != 4 or not week_s.startswith('W'):
            return err_bad_form(weekdate)

        year = tryparseint(year_s[1:3])
        if year.is_err():
            return Err('\'{}\': failed to parse year YY as int. {}'.format(weekdate, bad_form_msg))
        year = 2000 + year.ok()

        season_letter = year_s[-1]
        if season_letter not in 'SMFW':
            return Err('\'{}\': failed to parse season letter [SMFW]. {}'.format(weekdate, bad_form_msg))

        season_key = '{}-{}'.format(year, season_letter)
        if season_key not in self.seasons:
            return Err('\'{}\': failed to retrieve season date'.format(weekdate))
        season_datetup = self.seasons[season_key]
        season_date = datetime.date(*season_datetup)
        season_week = season_date.isocalendar()[1]

        week = tryparseint(week_s[1:-1])
        if week.is_err():
            return Err('\'{}\': failed to parse week number as int. {}'.format(weekdate, bad_form_msg))
        week = week.unwrap()

        day_name = Seasons.to_longday(week_s[-1])
        if day_name.is_err():
            return Err('\'{}\': failed to expand short day \'{}\' code [MTWRFSU]. {}'.format(weekdate, week_s[-1], bad_form_msg))
        day_name = day_name.unwrap()
        day_offset = Seasons.dayoffset(day_name).unwrap()

        # print(weekdate, '::', 'y', year, 'seaweek', season_week, 'week', week,  'sum', season_week + week - 1, 
        #       'sd', season_date, 'do', day_offset)

        # we can figure the date by simply incrementing weeks and days. ISO8601 also assumes Monday is start of day.
        return Ok(season_date + datetime.timedelta(weeks=week-1, days=day_offset))

    @staticmethod
    def day_to_short_map() -> List[Tuple[str, str]]:
        return [
            ('Monday',        'M'),
            ('Tuesday',       'T'),
            ('Wednesday',     'W'),
            ('Thursday',      'R'),
            ('Friday',        'F'),
            ('Saturday',      'S'),
            ('Sunday',        'U'),
        ]

    @staticmethod
    def to_shortday(day: str) -> Result[str, str]:
        for (lday, sday) in Seasons.day_to_short_map():
            if lday == day:
                return Ok(sday)
        return Err('\'{}\': could not map day to short version'.format(day))

    @staticmethod
    def to_longday(day: str) -> Result[str, str]:
        for (lday, sday) in Seasons.day_to_short_map():
            if sday == day:
                return Ok(lday)
        return Err('\'{}\': could not map short day to long version'.format(day))

    @staticmethod
    def dayoffset(day: str) -> Result[int, str]:
        """
        given a day in long format (ex: 'Thursday'), return an offset where 'Monday' starts as 0
        """
        for (i, (lday, sday)) in enumerate(Seasons.day_to_short_map()):
            if lday == day:
                return Ok(i)
        return Err('\'{}\': could not parse long day to get offset'.format(day))

    @staticmethod
    def datetup_of(date: datetime.date) -> Tuple[int, int, int]:
        return (date.year, date.month, date.day)

def main(args: argparse.Namespace):
    seasons = Seasons()
    if args.subcommand == 'iso':
        print(seasons.parse_weekdate(args.week_date).unwrap())
    if args.subcommand == 'of':
        print(seasons.weekdate_of(datetime.date.fromisoformat(args.date)))
    if args.subcommand == 'today':
        today = datetime.date.today()
        print('{}  {}'.format(today, seasons.weekdate_of(today)))


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True

    sp = subparsers.add_parser('iso', help='convert a week date to a YYYY-MM-DD')
    sp.add_argument("week_date", help="A week date. Example: Y21M-W13M for Monday Week 13 of Summer 2021")

    sp = subparsers.add_parser('of', help='convert YYYY-MM-DD to a week date')
    sp.add_argument("date", help="date format in YYYY-MM-DD")

    sp = subparsers.add_parser('today', help='display both iso and week dates for today')
    sp = subparsers.add_parser('unittest', help='run the unit tests instead of main')

    return(p.parse_args())

def _main():
    if sys.version_info<(3,5,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)

    # if you have unittest as part of the script, you can forward to it this way
    if len(sys.argv) >= 2 and sys.argv[1] == 'unittest':
        import unittest
        sys.argv[0] += ' unittest'
        sys.argv.remove('unittest')
        print(sys.argv)
        unittest.main()
        exit(0)

    args = cmdline_args()
    main(args)


class WkdateTests(unittest.TestCase):
    def test_get_weekdate_typical(self):
        seasons = Seasons()
        self.assertEqual(seasons.weekdate_of(datetime.date(2021, 9, 13)), 'Y21M-W14M')
        self.assertEqual(seasons.weekdate_of(datetime.date(2021, 9, 12)), 'Y21M-W13U')

    def test_parse_weekdate_typical(self):
        seasons = Seasons()
        self.assert_weekdate_parses(seasons, 'Y21M-W14M', datetime.date(2021, 9, 13))
        self.assert_weekdate_parses(seasons, 'Y21M-W14T', datetime.date(2021, 9, 14))
        self.assert_weekdate_parses(seasons, 'Y19M-W1M', datetime.date(2019, 6, 17)) # actually before first day of summer
        self.assert_weekdate_parses(seasons, 'Y19M-W1U', datetime.date(2019, 6, 23))

    def assert_weekdate_parses(self, seasons: Seasons, weekdate: str, exp: datetime.date):
        res = seasons.parse_weekdate(weekdate)
        if res.is_err():
            self.fail('Unexpected ParseError:\n' + res.err())
        self.assertEqual(res.ok(), exp)

    def test_prototype(self):
        seasons = Seasons()
        today_date = datetime.date.today()
        print('\ndebug(prototype): today is {} {}'.format(seasons.weekdate_of(today_date), today_date))
        print(seasons.get_seasons()['2021-F'])


if __name__ == '__main__':
    _main()
