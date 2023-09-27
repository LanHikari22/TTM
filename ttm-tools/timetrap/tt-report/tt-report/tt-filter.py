#!/usr/bin/env python3
"""
Given a JSON output of timetrap, this filters out notes matching a pattern, like grep -ev.
"""
import sys
import argparse
from typing import Dict, Optional
from result import Ok, Err, Result
import json
import datetime
import calendar
from enum import Enum

import importlib  
common = importlib.import_module("tt-report.lib.common")
# from .lib.common import *

def main(args: argparse.Namespace):
    json_data = sys.stdin.read()
    jsn = json.loads(json_data)

    # print(json.dumps(jsn, indent=4))
    print(format_default(jsn))

# ==================================================================================================
def define_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    # p.add_argument("format",
    #                 help="choice from: ")
    #  p.add_argument("required_int", type=int,
                   #  help="req number")
    #  p.add_argument("--on", action="store_true",
                   #  help="include to enable")
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
class UnitTests(CommonTestCase):
    def test_dummy(self):
        self.assertEqual("dummy" != 0)

if __name__ == '__main__':
    _main()
