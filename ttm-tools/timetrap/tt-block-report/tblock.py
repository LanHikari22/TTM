#!/usr/bin/env python3
"""
"""
import sys
import argparse
from typing import Any, Dict, MutableMapping, Optional, Tuple, overload
from result import Ok, Err, Result
from enum import Enum

class Stat:
    """
    Represents an int tuple (done, expected)
    """
    def __init__(self, done: int, expected: Optional[int]=None):
        self.done = done
        self.expected = expected

    def __str__(self) -> str:
        if self.expected is not None:
            return '{}/{}'.format(self.done, self.expected)
        else:
            return '{}'.format(self.done)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, o: object) -> bool:
        if type(o) is Stat:
            return self.done == o.done and self.expected == o.expected
        return False

    class ParseError(Enum):
        OK = 0
        MultipleOutOfError = 1
        EmptyError = 2
        IntParseError = 3
        NegativeError = 4
        DoneMissingError = 5

        def with_ctx(self, ctx: Dict[str, Any]):
            self.ctx = ctx
            self.ctx.setdefault('s', 's???')
            self.ctx.setdefault('val', 'val???')
            return self

        def __str__(self) -> str:
            return {
                Stat.ParseError.OK: 
                    'all OK',
                Stat.ParseError.MultipleOutOfError: 
                    '{}: cannot contain multiple /'.format(self.ctx['s']),
                Stat.ParseError.EmptyError: 
                    '{}: empty: must contain at least one value'.format(self.ctx['s']),
                Stat.ParseError.IntParseError: 
                    '{}: {} is not a valid int'.format(self.ctx['s'], self.ctx['val']),
                Stat.ParseError.NegativeError: 
                    '{}: {} must be non-negative'.format(self.ctx['s'], self.ctx['val']),
                Stat.ParseError.DoneMissingError: 
                    '{}: Done value must be present'.format(self.ctx['s']),
            }[self]


    @staticmethod
    def parse(s: str) -> Result['Stat', ParseError]:
        s = s.strip()
        if s == '':
            return Err(Stat.ParseError.EmptyError.with_ctx({'s': s}))
        
        values = s.split('/')
        
        if len(values) > 2:
            return Err(Stat.ParseError.MultipleOutOfError.with_ctx({'s': s}))
        if values[0] == '':
            return Err(Stat.ParseError.DoneMissingError.with_ctx({'s': s}))
        
        try:
            done = int(values[0])
        except ValueError:
            return Err(Stat.ParseError.IntParseError.with_ctx({'s': s, 'val': values[0]}))

        try:
            exp = None if len(values) == 1 else int(values[1])
        except ValueError:
            return Err(Stat.ParseError.IntParseError.with_ctx({'s': s, 'val': values[1]}))
        
        if done < 0:
            return Err(Stat.ParseError.NegativeError.with_ctx({'s': s, 'val': done}))
        if exp is not None and exp < 0:
            return Err(Stat.ParseError.NegativeError.with_ctx({'s': s, 'val': exp}))

        return Ok(Stat(done, exp))

class BlockStats:
    """
        tuple of stats to represent the time spent now, accumulative (recursive) and accum if it differs:
        (today, acc_recur, acc)
    """
    def __init__(self, today: Stat, acc: Stat=None, acc_recur: Stat=None):
        '''
        if `acc` is None, then it is assumed to equal acc_recur
        :raises ValueError: if both `acc` and `acc_recur` contain differing goals.
        :raises ValueError: if `acc_recur` does not sum to at least `acc`.
        '''
        self.today = today
        self.acc = acc
        self.acc_recur = acc_recur

        self.acc = Stat(0) if self.acc is None else self.acc
        self.acc_recur = self.acc if self.acc_recur is None else self.acc_recur

        if self.acc_recur.expected is not None:
            raise ValueError(BlockStats.ParseError.AccGoalsNotSameError)
        if self.acc_recur.done < self.acc.done:
            raise ValueError(BlockStats.ParseError.BadRecursiveAccSumError)



    
    def __str__(self) -> str:
        out: str = '(' + self.today

        def incl_if_applicable(stat: Stat):
            if stat.done != 0 or stat.expected is not None:
                return ', ' + stat
            return ','
        out += incl_if_applicable(self.acc)
        out += incl_if_applicable(self.acc_recur)

        out += ')'

        return out.replace(',,)', ')')


    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, o: object) -> bool:
        if type(o) is BlockStats:
            return self.today == o.today and self.acc == o.acc and self.acc_recur == o.acc_recur
        return False

    class ParseError(Enum):
        OK = 0
        StatParseError = 1
        BadFormError = 2
        BadRecursiveAccSumError = 3
        AccGoalsNotSameError = 4

        def with_ctx(self, ctx: Dict[str, Any]):
            self.ctx = ctx
            self.ctx.setdefault('s', 's???')
            self.ctx.setdefault('val', 'val???')
            self.ctx.setdefault('statErr', 'statErr???')
            return self

        def __str__(self) -> str:
            return {
                BlockStats.ParseError.OK:
                    'all OK',
                BlockStats.ParseError.StatParseError:
                    '\'{}\': failed to parse stat: {}'.format(self.ctx['s'], self.ctx['statErr']),
                BlockStats.ParseError.BadFormError:
                    '\'{}\': Bad form. Expected (A[,B][,C])'.format(self.ctx['s']),
                BlockStats.ParseError.BadRecursiveAccSumError:
                    '\'{}\': Recursive acc must be >= acc'.format(self.ctx['s']),
                BlockStats.ParseError.AccGoalsNotSameError:
                    '\'{}\': acc and recur_acc must have the same goal'.format(self.ctx['s']),
            }[self]
    
    @staticmethod
    def parse(s: str) -> Result['BlockStats', ParseError]:
        s = s.strip()
        if s == '' or not s.startswith('(') or not s.endswith(')') or s.count(',') > 2:
            return Err(BlockStats.ParseError.BadFormError.with_ctx({'s': s}))
        s = s[1:-1]

        today, acc, recursive_acc = Stat(0), Stat(0), Stat(0)
        stats_s = s.split(',')
        assert len(stats_s) <= 3, 'BlockStats.parse(): already made a check on form'
        for i in range(len(stats_s)):
            res = Stat.parse(stats_s[i])
            if res.is_err():
                return Err(BlockStats.ParseError.StatParseError.with_ctx({'s': s}))

            if i == 0:
                today = res.ok()
            if i == 1:
                acc = res.ok()
            if i == 2:
                recursive_acc = res.ok()

        if recursive_acc.done < acc.done:
            return Err(BlockStats.ParseError.BadRecursiveAccSumError.with_ctx({'s': s}))
        if recursive_acc.expected is not None:
            return Err(BlockStats.ParseError.AccGoalsNotSameError.with_ctx({'s': s}))
        
        return Ok(BlockStats(today, acc, recursive_acc))



def main(args: argparse.Namespace):
    pass

def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True
    sp = subparsers.add_parser('report')
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


import unittest

class CommonTestUtils(unittest.TestCase):
    @staticmethod
    def assertError(tc: unittest.TestCase, act: Result[Any, Any], exp: Result[Any, Any]):
        assert exp.is_err()
        tc.assertTrue(act.is_err())
        if act.is_err():
            tc.assertEqual(act, exp, str(act.err()))

class StatTests(unittest.TestCase):
    def test_parses_typical(self):
        self.assertEqual(Stat.parse('1/5'), Ok(Stat(1, 5)))
        self.assertEqual(Stat.parse('3333'), Ok(Stat(3333, None)))

    def test_fails_parsing(self):
        self.assertError(Stat.parse('1/5/4'), Err(Stat.ParseError.MultipleOutOfError))
        self.assertError(Stat.parse(''), Err(Stat.ParseError.EmptyError))
        self.assertError(Stat.parse('apples/9'), Err(Stat.ParseError.IntParseError))
        self.assertError(Stat.parse('-9/9'), Err(Stat.ParseError.NegativeError))
        self.assertError(Stat.parse('/5'), Err(Stat.ParseError.DoneMissingError))

    def assertError(self, act: Result[Any, Any], exp: Result[Any, Any]):
        CommonTestUtils.assertError(self, act, exp)

class BlockStatsTests(unittest.TestCase):
    def test_parses_typical(self):
        self.assertEqual(BlockStats.parse('(1/5)'), Ok(BlockStats(Stat(1, 5))))
        self.assertEqual(BlockStats.parse('(3333)'), Ok(BlockStats(Stat(3333))))
        self.assertEqual(BlockStats.parse('(0,5/2)'), Ok(BlockStats(Stat(0), Stat(5, 2))))
        self.assertEqual(BlockStats.parse('(0/1,5/2,9/2)'), Ok(BlockStats(Stat(0,1), Stat(5, 2), Stat(9))))
        self.assertEqual(BlockStats.parse('(,,4)'), Ok(BlockStats(Stat(0), Stat(0), Stat(4))))

    def test_fails_parsing(self):
        self.assertError(BlockStats.parse(''), Err(BlockStats.ParseError.BadFormError))
        self.assertError(BlockStats.parse('(beep]'), Err(BlockStats.ParseError.BadFormError))
        self.assertError(BlockStats.parse('(0,0,0,0)'), Err(BlockStats.ParseError.BadFormError))
        self.assertError(BlockStats.parse('(0,1,0)'), Err(BlockStats.ParseError.BadRecursiveAccSumError))
        self.assertError(BlockStats.parse('(0,1,0/3)'), Err(BlockStats.ParseError.AccGoalsNotSameError))
        self.assertError(BlockStats.parse('(0,1,0/3)'), Err(BlockStats.ParseError.AccGoalsNotSameError))

    def assertError(self, act: Result[Any, Any], exp: Result[Any, Any]):
        CommonTestUtils.assertError(self, act, exp)
    

if __name__ == '__main__':
    _main()