#!/bin/python3

import sys
import os
import subprocess
import re
import fileinput
import importlib.util
from importlib import import_module
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
import pipe
import argparse
from datetime import datetime as dtdt

spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.note-parser.py")
note_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_parser)
ntp = note_parser

log_file = '/tmp/citations-processor.log'


def log_any(s, status, verbose_level):
    if g_args.verbose < verbose_level:
        return

    with open(log_file, 'a') as f:
        f.write(str(dtdt.today()) + f' {status} - ' + s + '\n')


def log_error(s): return log_any(s, 'ERROR', verbose_level=0)
def log_info(s): return log_any(s, 'INFO', verbose_level=1)
def log_warn(s): return log_any(s, 'WARN', verbose_level=1)
def log_debug(s): return log_any(s, 'DEBUG', verbose_level=2)
def log_trace(s): return log_any(s, 'TRACE', verbose_level=3)


def cluster_items_by_objective(parsed_items):

    groups = []
    cur_group = []

    for lineno, item in parsed_items:
        if item.item_type == ntp.ItemType.OBJECTIVE_LINE:
            # add the current group (if non empty) to groups
            if len(cur_group) > 0:
                groups.append(cur_group)
                cur_group = []
        else:
            # skip until we at least have a defined group with an objective in it first
            if len(cur_group) == 0:
                continue


        cur_group.append((lineno, item))

    return groups


def process_task_notelog_entires_for_file(filename: str, clustered=False):
    parsed_items = ntp.process_note_file(filename, incl_logs=True)
    task_grouped = cluster_items_by_objective(parsed_items)

    for i in range(len(task_grouped)):
        if len(task_grouped[i]) <= 1:
            continue

        first_lineno, first_item = task_grouped[i][0]

        if not clustered:
            for lineno, item in task_grouped[i][1:]:
                desc = item.get_part(ntp.ItemType.KV, key='desc').value['desc'].strip()

                # one word descriptions are usually just section names. Not very informative for us.
                if len(desc.split(' ')) < 2:
                    continue

                # Here we print the task with the same lineno as the notelog so that it is the
                # priority to go to.
                print(filename + ':' + str(lineno) + ':' + first_item.value.strip())

                item_val = item.value.replace('\n\n', '\n').strip()

                for line in item_val.split('\n'):
                    line = line.strip()
                    if line:
                        print(filename + ':' + str(lineno) + ':\t' + line)

                print('/ENTRY')

        else: # clustered
            # Initially, we specify the task
            print(filename + ':' + str(first_lineno) + ':' + first_item.value.strip())

            for lineno, item in task_grouped[i][1:]:
                desc = item.get_part(ntp.ItemType.KV, key='desc').value['desc'].strip()

                # one word descriptions are usually just section names. Not very informative for us.
                if len(desc.split(' ')) < 2:
                    continue

                item_val = item.value.replace('\n\n', '\n').strip()

                for line in item_val.split('\n'):
                    line = line.strip()
                    if line:
                        print(filename + ':' + str(lineno) + ':\t' + line)

            # Finally, all these lines are out entry.
            print('/ENTRY')


def main(args: argparse.Namespace):
    log_debug(f'args: {args}')

    directory = args.directory

    import os
    from glob import glob
    filenames = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*'))]

    for filename in filenames:
        try:
            if '.git' in filename:
                continue

            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                if args.subcommand == 'group-task-notelog':
                    process_task_notelog_entires_for_file(filename, clustered=args.clustered)
        except UnicodeDecodeError:
            pass
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            log_error(f'Reached an error while processing filename {filename}:\n{error_trace}')


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument("directory",
                   help="Location to search in")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help="Increase verbosity level (use -v, -vv, or -vvv)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True

    sp = subparsers.add_parser('group-task-notelog', 
                               help='Generates task-notelog entries for multiline grep')
    sp.add_argument("--clustered", action="store_true",
                    help="Show only one entry per task with multiple notelogs")

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
    global g_args
    g_args = args
    main(args)


if __name__ == '__main__':
    _main()