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

try:
    spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.note-parser.py")
    note_parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(note_parser)
except Exception:
    spec=importlib.util.spec_from_file_location("note_parser","tmlib.note-parser.py")
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


def cluster_items_by_objective(parsed_items, cb_filter_items=None):

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

        # callback to filter items in the group. Though a group of one task should be guaranteed.
        if item.item_type != ntp.ItemType.OBJECTIVE_LINE:
            if cb_filter_items and not cb_filter_items(item):
                continue

        cur_group.append((lineno, item))

    return groups


def process_task_notelog_entries_for_file(filename: str, clustered=False):
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


def item_contains_cite_code(item):
    desc = ntp.get_kv(item, 'desc')

    cite_code_item = ntp.Item.parse(ntp.ItemType.CITE_CODE, desc)
    if not cite_code_item:
        return False
    
    return True
    
def item_contains_parent_cite_code(item):
    desc = ntp.get_kv(item, 'desc')

    cite_code = ntp.Item.parse(ntp.ItemType.CITE_CODE, desc)
    if not cite_code:
        return False
    
    codes = ntp.get_kv(cite_code, 'code')
    if len(codes) < 2:
        return False
    
    if codes[0] in ['P', 'PRJ']:
        return True
    
    return False


def item_contains_nonparent_cite_code(item):
    return item_contains_cite_code(item) and \
       not item_contains_parent_cite_code(item)


def _format_note_desc(note_item):
    note_item_value = note_item.value.strip()
    if '\n' in note_item_value:
        note_item_value = note_item_value.replace('\n\n', '\n')
    
    return note_item_value


def process_task_notelog_ref_entries_for_file(filename: str, clustered=False):
    parsed_items = ntp.process_note_file(filename, incl_refs=True, incl_logs=True)

    task_parsed_items = parsed_items \
        | pipe.filter(lambda lineno_item: lineno_item[1].item_type == ntp.ItemType.OBJECTIVE_LINE) \
        | pipe.Pipe(list)

    task_notes_parsed_items = parsed_items \
        | pipe.filter(lambda lineno_item: lineno_item[1].item_type == ntp.ItemType.OBJECTIVE_LINE or \
                                          lineno_item[1].item_type == ntp.ItemType.LOG_LINE) \
        | pipe.Pipe(list)

    task_notes_parsed_items = parsed_items \
        | pipe.filter(lambda lineno_item: lineno_item[1].item_type == ntp.ItemType.OBJECTIVE_LINE or \
                                          lineno_item[1].item_type == ntp.ItemType.LOG_LINE) \
        | pipe.Pipe(list)

    task_refs_parsed_items = parsed_items \
        | pipe.filter(lambda lineno_item: lineno_item[1].item_type == ntp.ItemType.OBJECTIVE_LINE or \
                                          lineno_item[1].item_type == ntp.ItemType.CITATION_LINE) \
        | pipe.Pipe(list)


    task_notes_grouped = cluster_items_by_objective(task_notes_parsed_items, item_contains_nonparent_cite_code)
    task_notes_parent_grouped = cluster_items_by_objective(task_notes_parsed_items, item_contains_parent_cite_code)
    task_refs_grouped = cluster_items_by_objective(task_refs_parsed_items)

    if len(task_parsed_items) == 0:
        return

    # The entries cover the Tasks x Citations space, so there is always a task and a citation.
    #   It should be exactly tasks_refs_grouped.
    for i_grp in range(len(task_refs_grouped)):
        if len(task_refs_grouped[i_grp]) <= 1:
            # We will not accept tasks with no refs.
            continue

        # Parse the task
        task_lineno, task_item = task_refs_grouped[i_grp][0]
        task_uuid = ntp.get_tag(task_item, 'uuid')

        # Now let's process the group ref items
        for ref_lineno, ref_item in task_refs_grouped[i_grp][1:]:
            if ref_item.item_type != ntp.ItemType.CITATION_LINE:
                log_error(f'Encountered {ref_item.item_type} when we only expect CITATION_LINE')
                return
            
            desc = ntp.get_kv(ref_item, 'desc')

            cite_code = ref_item.get_part(ntp.ItemType.CITE_CODE)
            if not cite_code:
                log_error('Citation line must have a cite_code')
                return
            
            # Search the user notelogs for presence of this cite_code
            if not clustered:
                found = False
                for note_lineno, note_item in task_notes_grouped[i_grp]:
                    note_desc = ntp.get_kv(note_item, 'desc')

                    if cite_code.value in note_desc:
                        found = True
                        print(filename + ':' + str(note_lineno) + ':' + task_item.value.strip())
                        print(filename + ':' + str(note_lineno) + ':' + ref_item.value.strip())
                        print(filename + ':' + str(note_lineno) + ':' + _format_note_desc(note_item))
                        print('/ENTRY')
                
                if not found:
                    print(filename + ':' + str(ref_lineno) + ':' + task_item.value.strip())
                    print(filename + ':' + str(ref_lineno) + ':' + ref_item.value.strip())
                    print('/ENTRY')
                
            else:
                # This is clustered by notelog
                notelogs = []
                for note_lineno, note_item in task_notes_grouped[i_grp]:
                    note_desc = ntp.get_kv(note_item, 'desc')

                    if cite_code.value in note_desc:
                        notelogs.append(filename + ':' + str(ref_lineno) + ':' + _format_note_desc(note_item))
                
                print(filename + ':' + str(ref_lineno) + ':' + task_item.value.strip())
                print(filename + ':' + str(ref_lineno) + ':' + ref_item.value.strip())
                if len(notelogs) != 0: # This was here before, because we only printed the task/ref if notelogs are found.
                    for notelog in notelogs:
                        print(notelog)
                print('/ENTRY')

        # Now let's process the non-obvious cases. notelogs can refer to citations from the parent branch!
        task_branch = ntp.find_parent_branch_items(task_parsed_items, task_lineno)

        for parent_task_lineno, parent_task in task_branch:
            i_prn_grp = None

            # Reverse find the index for the parent to search the groups
            for j_grp in range(len(task_refs_grouped)):
                if len(task_refs_grouped[j_grp]) <= 1:
                    # We will not accept tasks with no refs.
                    continue

                # Parse the task
                parent_lineno, parent_item = task_refs_grouped[j_grp][0]

                if parent_lineno == parent_task_lineno:
                    i_prn_grp = j_grp
                    break
            
            if i_prn_grp == None:
                # Could not find a parent with refs.
                continue

            # Now we process this parent's references
            for ref_lineno, ref_item in task_refs_grouped[i_prn_grp][1:]:
                if ref_item.item_type != ntp.ItemType.CITATION_LINE:
                    log_error(f'Encountered {ref_item.item_type} when we only expect CITATION_LINE')
                    return
                
                parent_cite_code = ref_item.get_part(ntp.ItemType.CITE_CODE)
                if not parent_cite_code:
                    log_error('Citation line must have a cite_code')
                    return
                
                # Now we search the current task's parent-referencing notelogs to see if they match
                # any parent_cite_code
                if not clustered:
                    for note_lineno, note_item in task_notes_parent_grouped[i_grp]:
                        note_desc = ntp.get_kv(note_item, 'desc')

                        if parent_cite_code.value in note_desc or \
                           parent_cite_code.value.replace('^', '^P::') in note_desc or \
                           parent_cite_code.value.replace('^', '^PRJ::') in note_desc:
                            print(filename + ':' + str(note_lineno) + ':' + task_item.value.strip())
                            print(filename + ':' + str(note_lineno) + ':' + parent_task.value.strip())
                            print(filename + ':' + str(note_lineno) + ':' + ref_item.value.strip())
                            print(filename + ':' + str(note_lineno) + ':' + _format_note_desc(note_item))
                            print('/ENTRY')
                else:
                    # This is clustered by notelog
                    notelogs = []
                    for note_lineno, note_item in task_notes_parent_grouped[i_grp]:
                        note_desc = ntp.get_kv(note_item, 'desc')

                        if parent_cite_code.value in note_desc or \
                           parent_cite_code.value.replace('^', '^P::') in note_desc or \
                           parent_cite_code.value.replace('^', '^PRJ::') in note_desc:
                            notelogs.append(filename + ':' + str(ref_lineno) + ':' + _format_note_desc(note_item))
                    
                    if len(notelogs) != 0:
                        print(filename + ':' + str(ref_lineno) + ':' + task_item.value.strip())
                        print(filename + ':' + str(ref_lineno) + ':' + parent_task.value.strip())
                        print(filename + ':' + str(ref_lineno) + ':' + ref_item.value.strip())
                        for notelog in notelogs:
                            print(notelog)
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
    log_debug('==================================================================================')
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
            
            log_debug(f'filename: {filename}')

            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                if args.subcommand == 'group-task-notelog':
                    process_task_notelog_entries_for_file(filename, clustered=args.clustered)

                if args.subcommand == 'parse-citation-dataset':
                    df = parse_citation_dataset(filename)
                    if df_tot is None:
                        df_tot = df
                    else:
                        df_tot = pd.concat([df_tot, df], ignore_index=True)

                if args.subcommand == 'group-task-notelog-reference':
                    process_task_notelog_ref_entries_for_file(filename, clustered=args.clustered)

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

    sp = subparsers.add_parser('group-task-notelog-reference', 
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
