#!/usr/bin/env python3
import sys
import argparse
import subprocess

class TimeTrapEntry:
    def __init__(id: int, day: str, start: str, end: str, dur: str, desc: str):
        self.id = id
        self.day = day
        self.start = start
        self.end = end
        self.dur = dur
        self.desc = desc

def main(args: argparse.Namespace):
    print(args, args.verbosity)

def define_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument("required_positional_arg",
                   help="desc")
    p.add_argument("required_int", type=int,
                   help="req number")
    p.add_argument("--on", action="store_true",
                   help="include to enable")
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True # must select a subcommand!

    sp = subparsers.add_parser('actionA', help="does something cool")
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

    main(define_args())

import unittest
class UnitTests(unittest.TestCase):
   def test_something(self):
       self.assertTrue(True, "rigorous test :)")

   def test_prototype(self):
       out = subprocess.check_output('timetrap -v d', shell=True)
       

       os.system('timetrap -v d')


if __name__ == '__main__':
    _main()
