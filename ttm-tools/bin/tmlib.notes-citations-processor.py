#!/bin/python3

import sys
import os
import subprocess
import re
import fileinput
import importlib.util
import unittest
from importlib import import_module
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
import pipe
import argparse
import pandas as pd
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


def sha256_hash(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()[:8]

def process_global_node_id(item, category, desc):
    # First, check if the node has a uuid, then that will be its unique node_id
    uuid = ntp.get_kv(item, 'uuid')
    if uuid:
        return 'T:' + uuid
    
    # If no UUID is found, we can only rely on the presence of the category and desc.
    return 'N:' + sha256_hash(category + desc)
    

def parse_citation_dataset(filename: str) -> pd.DataFrame:
    parsed_items = ntp.process_note_file(filename, incl_refs=True)
    task_grouped = cluster_items_by_objective(parsed_items)

    records = []

    for i in range(len(task_grouped)):
        if len(task_grouped[i]) <= 1:
            continue

        _, first_item = task_grouped[i][0]

        task_datetime = first_item.get_part(ntp.ItemType.TIME_DATE)

        task_tags = first_item.get_part(ntp.ItemType.TAGS)
        if not task_tags:
            continue

        uuid = ntp.get_kv(task_tags, 'uuid')
        if uuid == None:
            continue
        log_debug(f'task uuid: {uuid}')

        for lineno, item in task_grouped[i][1:]:
            if item.item_type != ntp.ItemType.CITATION_LINE:
                continue

            time_date = item.get_part(ntp.ItemType.TIME_DATE)
            cite_code = item.get_part(ntp.ItemType.CITE_CODE)
            relations = item.get_part(ntp.ItemType.CITE_RELATION)
            desc = ntp.get_kv(item, 'desc').strip()

            # Figure out the category for the subject_node
            codes = ntp.get_kv(cite_code, 'code')
            if type(codes) is list:
                category = codes[-1]
            else:
                category = codes
            
            # Figure out the global node_id for this citation
            node_id = process_global_node_id(item, category, desc)

            record = {
                'filename': filename,
                'lineno': lineno,
                'node_uuid': node_id,
                'datetime': time_date.value,
                'task_datetime': task_datetime.value,
                'task_uuid': uuid, 
                'subject_node': cite_code.value, 
                'category': category,
            }

            if relations is None:
                record = {**record, **{
                    'object_node': None,
                    'relation': None,
                    'is_from': None,
                    'status': None,
                }}
            elif type(relations) is list:
                for relation in relations:
                    record = {**record, **{
                        'object_node': ntp.get_kv(relation, 'node'), 
                        'relation': ntp.get_kv(relation, 'relation'), 
                        'is_from': ntp.get_kv(relation, 'is_from'),
                        'status': ntp.get_kv(relation, 'status'),
                    }}
            else:
                record = {**record, **{
                    'object_node': ntp.get_kv(relations, 'node'), 
                    'relation': ntp.get_kv(relations, 'relation'), 
                    'is_from': ntp.get_kv(relations, 'is_from'),
                    'status': ntp.get_kv(relations, 'status'),
                }}
            
            record = {**record, **{'desc': desc}}
            records.append(record)
    
    return pd.DataFrame.from_records(records)

def main(args: argparse.Namespace):
    log_debug(f'args: {args}')

    directory = args.directory

    import os
    from glob import glob
    filenames = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*'))]

    # Some commands may want to accumulate a dataset across multiple files
    df_tot = None

    for filename in filenames:
        try:
            if '.git' in filename:
                continue

            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                if args.subcommand == 'group-task-notelog':
                    process_task_notelog_entires_for_file(filename, clustered=args.clustered)

                if args.subcommand == 'parse-citation-dataset':
                    df = parse_citation_dataset(filename)
                    if df_tot is None:
                        df_tot = df
                    else:
                        df_tot = pd.concat([df_tot, df], ignore_index=True)

        except UnicodeDecodeError:
            pass
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            log_error(f'Reached an error while processing filename {filename}:\n{error_trace}')
    
    if df_tot is not None:
        df_tot.to_csv(args.csv_df_filename)


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

    sp = subparsers.add_parser('parse-citation-dataset', 
                               help='Parses a table of citations from the files in the directory given')
    sp.add_argument("csv_df_filename",
                    help="Where to save the output dataset")

    return(p.parse_args())


def _main():
    if sys.version_info<(3,5,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)

    global g_args
    # if you have unittest as part of the script, you can forward to it this way
    if len(sys.argv) >= 2 and sys.argv[1] == 'unittest':
        import unittest
        sys.argv[0] += ' unittest'
        sys.argv.remove('unittest')

        class Args:
            def __init__(self):
                self.verbose = 2
        g_args = Args()

        log_debug('Running unit tests')

        unittest.main()
        exit(0)

    args = cmdline_args()
    g_args = args
    main(args)

class UnitTests(unittest.TestCase):
    def test_manual_can_parse_citation_dataset(self):
        # Input some file here to test. The below is not guaranteed to exit on your system.
        filename = '/root/notes/projects/TTM1-ttm_dev'

        # Enable the manual test
        test_enabled = False
        if not test_enabled:
            return

        df = parse_citation_dataset(filename)
        df.to_csv('/tmp/df.csv')
        print(df)

if __name__ == '__main__':
    _main()
