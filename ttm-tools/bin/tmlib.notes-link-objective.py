#!/bin/python3

import os
import sys
import subprocess
import re
import fileinput
import importlib.util
from importlib import import_module
from enum import Enum, auto
from typing import List, Optional, Tuple
import unittest
import argparse
import pipe
import tempfile
import shutil

log_file = '/tmp/note-link-objective.log'
log_echo_stdout = True

def log_any(s, status, verbose_level):
    from datetime import datetime as dtdt

    if g_args.verbose < verbose_level:
        return

    with open(log_file, 'a') as f:
        s = str(dtdt.today()) + f' {status} - ' + s
        f.write(s + '\n')
        if log_echo_stdout:
            print(s)


def log_error(s): return log_any(s, 'ERROR', verbose_level=0)
def log_info(s): return log_any(s, 'INFO', verbose_level=1)
def log_warn(s): return log_any(s, 'WARN', verbose_level=1)
def log_debug(s): return log_any(s, 'DEBUG', verbose_level=2)
def log_trace(s): return log_any(s, 'TRACE', verbose_level=3)

spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.note-parser.py")
note_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_parser)
ntp = note_parser

spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.notes-register-objective.py")
notes_register_objective = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes_register_objective)
nro = notes_register_objective

prn_error = log_error
prn_warn = log_warn

def _try_parse_int(s):
    try:
        return int(s)
    except Exception:
        return None


def _add_or_increment_refd(item):
    tags = item.get_part(ntp.ItemType.TAGS)
    if not tags:
        return ('NO_TAGS', None)
    
    tags_kvs = tags.get_part(ntp.ItemType.KV)
    if type(tags_kvs) != list:
        tags_kvs = [tags_kvs]
    
    tags_s = ntp.get_kv(tags, 'tag')

    refd_tag = None
    if type(tags_s) is list:
        for tag in tags_s: 
            if tag.startswith('refd='):
                refd_tag = tag
            pass
    else:
        if tags_s.startswith('refd='):
            refd_tag = tags_s
    
    if refd_tag is None:
        # We need to add one.
        new_refd_tag = ntp.Item(ntp.ItemType.KV, {'tag': 'refd=1'}, [])

        # Create new tags with this
        new_tags = ntp.Item(ntp.ItemType.TAGS, tags.value, tags_kvs + [new_refd_tag])
    else:
        # We need to increment.

        refd_tag_split = refd_tag.split('=')
        if len(refd_tag_split) != 2:
            return ('INVALID_REFD', None)
        n = _try_parse_int(refd_tag_split[1])
        if n is None:
            return ('INVALID_REFD', None)

        new_refd_tag = ntp.Item(ntp.ItemType.KV, {'tag': f'refd={n+1}'}, [])

        # Remove the previous refd tag KV
        for kv in tags_kvs:
            if 'tag' in kv.value and 'refd=' in kv.value['tag']:
                tags_kvs.remove(kv)
                break
        
        new_tags = ntp.Item(ntp.ItemType.TAGS, tags.value, tags_kvs + [new_refd_tag])
    
    return ('OK', new_tags)


def _process_refs_for_item_at_lineno(item_lineno, parsed_items_with_refs):
    result_ref_lineno_items = []
    for lineno, item in parsed_items_with_refs:
        if lineno <= item_lineno:
            continue

        if item.item_type == ntp.ItemType.CITATION_LINE:
            result_ref_lineno_items.append((lineno, item))

        if item.item_type == ntp.ItemType.OBJECTIVE_LINE:
            break
    
    return result_ref_lineno_items


def _process_next_task(item_lineno, parsed_items_with_refs):
    for lineno, item in parsed_items_with_refs:
        if lineno <= item_lineno:
            continue
            
        if item.item_type == ntp.ItemType.OBJECTIVE_LINE:
            return (True, lineno, item)
    return (False, None, None)


def build_normal_task_link_ref_line(item, uuid, pinned_item, opt_last_number, ttm_timedate):
    if not opt_last_number:
        last_number = 1
    else:
        last_number = opt_last_number + 1
    
    tab_level = pinned_item.get_part(ntp.ItemType.TAB_LEVEL)
    if not tab_level:
        return ('Failed to parse tab level', '')
    tab_level = tab_level.value

    desc = ntp.get_kv(item, 'desc')

    result = f'{tab_level}- {ttm_timedate} - [^T{last_number}]: {desc} #{uuid}'

    return ('OK', result)


def build_has_milestone_link_ref_line(item, uuid, pinned_item, opt_last_number, ttm_timedate):
    if not opt_last_number:
        last_number = 1
    else:
        last_number = opt_last_number + 1
    
    tab_level = pinned_item.get_part(ntp.ItemType.TAB_LEVEL)
    if not tab_level:
        return ('Failed to parse tab level', '')
    tab_level = tab_level.value
    tab_level = tab_level.replace('\t', '    ')

    desc = ntp.get_kv(item, 'desc')

    result = f'{tab_level}- {ttm_timedate} - [^T{last_number}]: /T::has_milestone/ {desc} #{uuid}'
 
    return ('OK', result)


def build_milestone_of_link_ref_line(item, uuid, pinned_item, opt_last_number, ttm_timedate):
    if not opt_last_number:
        last_number = 1
    else:
        last_number = opt_last_number + 1
    
    tab_level = pinned_item.get_part(ntp.ItemType.TAB_LEVEL)
    if not tab_level:
        return ('Failed to parse tab level', '')
    tab_level = tab_level.value

    desc = ntp.get_kv(item, 'desc')

    result = f'{tab_level}- {ttm_timedate} - [^T{last_number}]: (-) /T::milestone_of/ {desc} #{uuid}'

    return ('OK', result)


def _compute_tab_level(item):
    # Compute the likely tab modification. In a priority of tab, mult3, mult2
    tab_level = item.get_part(ntp.ItemType.TAB_LEVEL).value
    extra_tab = ''
    if '\t' in tab_level:
        extra_tab = '\t'
    else: 
        for i in [2, 3]:
            if len(tab_level) % i == 0:
                extra_tab = ' ' * i
                break
    
    return extra_tab


def duplicate_file_into_temp(filename):
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', dir=os.path.dirname(filename))

    # Write the content to a temporary file
    with open(temp_file.name, 'w') as write_fp:
        with open(filename, 'r') as read_fp:
            write_fp.write(read_fp.read())
    
    return temp_file.name


def link_objective(source_filename_lineno, sink_filename_lineno, ttm_timedate, cb_ref_builder):
    source_filename = source_filename_lineno.split(':')[0]
    source_lineno = source_filename_lineno.split(':')[1]
    sink_filename = sink_filename_lineno.split(':')[0]
    sink_lineno = sink_filename_lineno.split(':')[1]

    source_lineno_n = _try_parse_int(source_lineno)
    sink_lineno_n = _try_parse_int(sink_lineno)
    if not source_lineno_n:
        log_error(f'Failed to parse sink lineno: {source_filename}:{source_lineno}')
        return
    if not sink_lineno_n:
        log_error(f'Failed to parse sink lineno: {sink_filename}:{sink_lineno}')
        return

    source_parsed_items = ntp.process_note_file(source_filename, incl_refs=True)
    cur_source_item = ntp.find_item_at_lineno(source_parsed_items, source_lineno_n)

    if sink_filename == source_filename:
        sink_parsed_items = source_parsed_items
    else:
        sink_parsed_items = ntp.process_note_file(sink_filename, incl_refs=True)
    cur_sink_item = ntp.find_item_at_lineno(sink_parsed_items, sink_lineno_n)

    # log_debug(f'SOURCE {source_lineno} {cur_source_item}')
    # log_debug(f'SINK {sink_lineno} {cur_sink_item}')

    # First, ensure that we really have valid objectives for sink and source
    if cur_source_item is None:
        log_error(f'Invalid source objective line (None) for {source_filename}:{source_lineno}')
        return
    if cur_sink_item is None:
        log_error(f'Invalid sink objective line (None) for {sink_filename}:{sink_lineno}')
        return
    if cur_source_item.item_type != ntp.ItemType.OBJECTIVE_LINE:
        log_error(f'Invalid source objective line ({cur_source_item.item_type}) for {source_filename}:{source_lineno}')
        return
    if cur_sink_item.item_type != ntp.ItemType.OBJECTIVE_LINE:
        log_error(f'Invalid sink objective line ({cur_sink_item.item_type}) for {sink_filename}:{sink_lineno}')
        return

    # Ensure that both tasks are registered, or register them.
    sink_uuid = ntp.get_tag(cur_sink_item, 'uuid')
    source_uuid = ntp.get_tag(cur_source_item, 'uuid')
    if source_uuid == '':
        log_warn(f'Warn: Cannot link unregistered source objective line. Will register {source_filename}:{source_lineno}')
        nro.register_objective(source_filename, source_lineno_n)
        return link_objective(source_filename_lineno, sink_filename_lineno, ttm_timedate, cb_ref_builder)
    if sink_uuid == '':
        log_warn(f'Warn: Cannot link unregistered sink objective line. Will register {sink_filename}:{sink_lineno}')
        nro.register_objective(sink_filename, sink_lineno_n)
        return link_objective(source_filename_lineno, sink_filename_lineno, ttm_timedate, cb_ref_builder)

    # Now Retrieve the source and sink item notelogs 
    sink_ref_lineno_items = _process_refs_for_item_at_lineno(sink_lineno_n, sink_parsed_items)

    # Check if sink already refers to the task in question, or find its last numbered task reference
    last_number = None
    last_numbered_sink_task_lineno_ref = None
    last_sink_task_lineno_ref = None
    last_nontask_lineno_ref = None
    for lineno, ref_item in sink_ref_lineno_items:
        cite_code = ref_item.get_part(ntp.ItemType.CITE_CODE)

        codes = ntp.get_kv(cite_code, 'code')
        if type(codes) is list:
            category = codes[-1]
        else:
            category = codes

        ns = ntp.get_kv(cite_code, 'n')
        if type(ns) is list:
            category_n = ns[-1]
        else:
            category_n = ns
        category_n = _try_parse_int(category_n)
        
        # T is the designated Task category
        if category != 'T':
            last_nontask_lineno_ref = (lineno, ref_item)
            continue

        if category_n is not None:
            if last_number is None:
                last_number = category_n
                last_numbered_sink_task_lineno_ref = (lineno, ref_item)
            elif category_n > last_number:
                last_number = category_n
                last_numbered_sink_task_lineno_ref = (lineno, ref_item)
            else:
                pass
        
        last_sink_task_lineno_ref = (lineno, ref_item)
    
    # Now let's figure out the item to pin the new content to
    pin_before = True
    extra_tab = ''
    new_sink_item_pinned_to = None
    new_sink_item_lineno_pinned_to = None
    if last_numbered_sink_task_lineno_ref is not None:
        # log_debug('Processing last numbered item')
        # log_debug(f'last numbered item tab_level: "{last_numbered_sink_task_lineno_ref[1].get_part(ntp.ItemType.TAB_LEVEL).value}"')
        pin_before = False
        new_sink_item_lineno_pinned_to = last_numbered_sink_task_lineno_ref[0]
        new_sink_item_pinned_to = last_numbered_sink_task_lineno_ref[1]
    elif last_sink_task_lineno_ref is not None:
        pin_before = False
        new_sink_item_lineno_pinned_to = last_sink_task_lineno_ref[0]
        new_sink_item_pinned_to = last_sink_task_lineno_ref[1]
    elif last_nontask_lineno_ref is not None:
        pin_before = False
        new_sink_item_lineno_pinned_to = last_nontask_lineno_ref[0]
        new_sink_item_pinned_to = last_nontask_lineno_ref[1]
    
    if new_sink_item_pinned_to is None:
        # We haven't found an appropriate reference to pin to, so place it somewhere before the next task
        # This is more appropriate by the convention that citations and new logs in general
        #   tend to come last in the task notelogs.
        valid, next_task_lineno, next_task_item = _process_next_task(sink_lineno_n, sink_parsed_items)
        if valid:
            log_warn('Could not find an appropriate place to pin new content. pinning before new task.')
            pin_before = True
            new_sink_item_pinned_to = next_task_item
            new_sink_item_lineno_pinned_to = next_task_lineno

            extra_tab = _compute_tab_level(next_task_item)

    if new_sink_item_pinned_to is None:
        # There isn't even a next task to pin it before... Just put it immediately after the task. 
        log_warn('Could not find an appropriate place to pin new content. Putting right after task.')
        pin_before = False
        new_sink_item_pinned_to = cur_sink_item
        new_sink_item_lineno_pinned_to = sink_lineno
        extra_tab = _compute_tab_level(cur_sink_item)
    
    if new_sink_item_pinned_to is None:
        log_error('Failed to find a spot to place new reference')
        return

    # log_debug(f'previous source item: {cur_source_item}')

    # Now that we're pinning to the sink task, let's also modify the source task tags. 
    # Increment its refd tag, or create a refd tag.
    ec_s, new_source_tags = _add_or_increment_refd(cur_source_item)
    if ec_s != 'OK':
        if ec_s == 'NO_TAGS':
            log_error(f'source objective line has no tags at {source_filename_lineno}')
        if ec_s == 'INVALID_REFD':
            log_error(f'Invalid refd detected for source objective line at {source_filename_lineno}')
    
    new_source_item_parts = cur_source_item.parts

    for part in new_source_item_parts:
        if part.item_type == ntp.ItemType.TAGS:
            new_source_item_parts.remove(part)
            break
    
    new_source_item_parts.append(new_source_tags)
    
    new_source_item = ntp.Item(ntp.ItemType.OBJECTIVE_LINE, cur_sink_item.value, new_source_item_parts)

    # log_debug(f'new source item: {new_source_item}')

    # Inplace modify the files with the new content. The prints in this loop are directed into the file.
    try:
        # Create temporary files in case our solution here fails and destroys the files!
        tmp_source_filename = duplicate_file_into_temp(source_filename)
        tmp_sink_filename = duplicate_file_into_temp(sink_filename)

        # For the source task, only modify the task definition
        for line in fileinput.input(source_filename, inplace=True):
            if line == cur_source_item.value:
                print(ntp.build_objective_line_item(new_source_item) + '\n', end='')
            else:
                print(line, end='')

        # For the sink task, add a new citation
        lineno = 0
        for line in fileinput.input(sink_filename, inplace=True):
            lineno += 1
            if lineno == new_sink_item_lineno_pinned_to:
                err_msg, new_line = cb_ref_builder(cur_source_item, source_uuid, new_sink_item_pinned_to, last_number, ttm_timedate)
                if err_msg != 'OK':
                    raise Exception(f'Could not process file modifications: {err_msg}')

                if pin_before:
                    print(extra_tab + new_line + '\n', end='')
                    print(line, end='')
                else:
                    print(line, end='')
                    print(extra_tab + new_line + '\n', end='')
            else:
                print(line, end='')
        
        log_info(f'Successfully modified source and sink files')
        os.remove(tmp_source_filename)
        os.remove(tmp_sink_filename)
    except Exception:
        log_error('An exception occured, corrupting the files we are modifying! Reverting back from backup.')
        shutil.move(tmp_source_filename, source_filename)
        shutil.move(tmp_sink_filename, sink_filename)
        raise 


def main(args: argparse.Namespace):
    # log_debug(f'===========================================================')
    # log_debug(f'Running App {args}')

    if args.subcommand == 'link-task':
        link_objective(args.source_filename_lineno, args.sink_filename_lineno, args.ttm_timedate, 
                       build_normal_task_link_ref_line)
    if args.subcommand == 'link-milestone-of':
        link_objective(args.sink_filename_lineno, args.source_filename_lineno, args.ttm_timedate, 
                       build_milestone_of_link_ref_line)
    if args.subcommand == 'link-has-milestone':
        link_objective(args.source_filename_lineno, args.sink_filename_lineno, args.ttm_timedate, 
                       build_has_milestone_link_ref_line)


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument('ttm_timedate',
                   help='Current timedate in TTM format. See GetWeekRelativeCustomDateString in ttm.vim.')
    p.add_argument('source_filename_lineno',
                   help='Source task filename:lineno')
    p.add_argument('sink_filename_lineno',
                   help='Sink task filename:lineno')
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help="Increase verbosity level (use -v, -vv, or -vvv)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True

    sp = subparsers.add_parser('unittest', 
                    help='run the unit tests instead of main')

    sp = subparsers.add_parser('link-task', 
                    help='Creates a link from source to sink task')

    sp = subparsers.add_parser('link-milestone-of', 
                    help='')

    sp = subparsers.add_parser('link-has-milestone', 
                    help='Creates a has-milestone reference in sink')

    sp = subparsers.add_parser('link-milestone-of', 
                    help='Creates a milestone-of reference in source')

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
    pass


if __name__ == '__main__':
    _main()