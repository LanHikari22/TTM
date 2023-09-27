#!/usr/bin/env python3
"""
Tracks the state of the pomo UI and executes commands based on that to work with WSL
"""

import sys
import os
import argparse
from enum import Enum
import time

def cmdline_args():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    #  p.add_argument("required_positional_arg",
                   #  help="desc")
    #  p.add_argument("required_int", type=int,
                   #  help="req number")
    #  p.add_argument("--on", action="store_true",
                   #  help="include to enable")
    p.add_argument("-v", "--verbosity", type=int, choices=[0,1,2], default=0,
                   help="increase output verbosity (default: %(default)s)")
                   

    return(p.parse_args())

def error(msg):
    print(msg)
    exit(1)

def main(args):

    ticks = 0
    prev_state = 0
    while True:
        parsed, state = PomoControl.read_state()
        if not parsed:
            error("failed to parse state")
        PomoControl.task(state, prev_state)
        #  print("{0} state: {1} -> {2}".format(ticks, prev_state, state))

        time.sleep(1)
        ticks += 1
        prev_state = state
    pass


class PomoState(Enum):
    INACTIVE = 0
    ACTIVE = 1
    PAUSED = 2
    DONE = 3

    @staticmethod
    def from_char(c) -> (bool, int):
        parsed = False
        if c == '?':
            return (True, PomoState.INACTIVE)
        if c == 'R':
            return (True, PomoState.ACTIVE)
        if c == 'P':
            return (True, PomoState.PAUSED)
        if c == 'B':
            return (True, PomoState.DONE)

        return (False, -1)

class TimeTrapControl:
    @staticmethod
    def out():
        pass
        #  os.system("timetrap out")

    @staticmethod
    def resume():
        pass
        #  os.system("timetrap resume")

class PomoControl:
    @staticmethod
    def read_state() -> (bool, PomoState):
        status = os.popen("pomo st").read()
        return PomoState.from_char(status[0])

    @staticmethod
    def task(sm: PomoState, prev_sm: PomoState):
        # trigger logic
        if   sm == PomoState.PAUSED and prev_sm != PomoState.PAUSED:
            PomoControl._on_paused()
        elif sm != PomoState.PAUSED and prev_sm == PomoState.PAUSED:
            PomoControl._on_unpaused()
        elif sm == PomoState.DONE and prev_sm != PomoState.DONE:
            PomoControl._on_finished()


    @staticmethod
    def _on_paused():
        TimeTrapControl.out()
        pass

    @staticmethod
    def _on_unpaused():
        TimeTrapControl.resume()
        pass

    @staticmethod
    def _on_started():
        TimeTrapControl.resume()
        pass

    @staticmethod
    def _on_finished():
        os.system("powershell.exe New-BurntToastNotification -Text EOT")
        TimeTrapControl.out()
        pass


if __name__ == '__main__':
    if sys.version_info<(3,5,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)
        
    try:
        args = cmdline_args()
        #  print(args)
    except Exception as ex:
        print('error: ' + str(ex))
        sys.exit(1)


    main(args)

