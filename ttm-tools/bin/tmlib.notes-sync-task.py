#!/bin/python3

import sys
import os
import subprocess
import re
import fileinput
import importlib.util
from importlib import import_module
from enum import Enum, auto
from typing import List, Optional, Tuple

spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.note-parser.py")
note_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_parser)
ntp = note_parser
#print(ntp.find_parent_item, ntp.Item)

spec=importlib.util.spec_from_file_location("reg_objective","/root/.local/bin/tmlib.notes-register-objective.py")
reg_objective = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg_objective)
rgo = reg_objective

prn_error = print
prn_warn = print
prn_info = print

def sync_task(filename, lineno) -> str:
    parsed_items = ntp.process_note_file(filename)
    cur_item = ntp.find_item_at_lineno(parsed_items, lineno)
    if not cur_item:
        prn_error(f'Failed to find item at lineno {lineno}')
        return ''

    print(cur_item)

    cur_item_uuid = ntp.get_tag(cur_item, 'uuid')
    if cur_item_uuid == '':
        # Nothing to do here
        prn_info('Task is not registered')
        return ''

    print(cur_item_uuid)

    # Get the task information from notes
    desc = cur_item.get_part(ntp.ItemType.KV, key='desc').value['desc'].strip()
    status = cur_item.get_part(ntp.ItemType.KV, key='status')
    if status:
        status = status.value['status']
    tags = cur_item.get_part(ntp.ItemType.TAGS)

    # Get the gcode and project from the notes filename
    basename = os.path.basename(filename)
    basename_split = basename.split('-')
    gcode = basename_split[0]
    proj = '-'.join(basename_split[1:])

    # The task may be in the projects, areas, or resources folder. These determine the tags for context. project is default visiblity.
    if basename == filename:
        prn_error('Please specify the path for whether this is in proj, areas, or resources.')
        return ''
    dirname = os.path.basename(filename.replace(basename, '')[:-1])
    extra_tags = ''
    if dirname == 'areas':
        extra_tags += '+inv +area'
    if dirname == 'resources':
        extra_tags += '+inv +res'

    # Get Task Information from TaskWarrior
    tw_desc = ntp.system_cmd(f'task _get {cur_item_uuid}.description')
    tw_status = ntp.system_cmd(f'task _get {cur_item_uuid}.status')
    tw_tags = ntp.system_cmd(f'task _get {cur_item_uuid}.tags').split(',')
    tw_proj = ntp.system_cmd(f'task _get {cur_item_uuid}.project')
    tw_gcode = ntp.system_cmd(f'task _get {cur_item_uuid}.gcode')

    # Check presence of desc prefix
    #print('tw_desc', tw_desc)
    #print('desc', desc)
    tw_desc_prefix = ''
    p = re.compile('([abcdef1234567890]{8})')
    m = p.match(tw_desc)
    if m:
        tw_desc_prefix = tw_desc.split(' ')[0]
        tw_desc = tw_desc.replace(tw_desc_prefix, '').strip()
    #print('tw_desc', tw_desc)
    #print('tw_desc_prefix', tw_desc_prefix)

    # Sync Description
    if desc != tw_desc:
        new_desc = tw_desc_prefix + ' ' + desc
        new_desc = new_desc.strip()
        #print('new_desc', new_desc)
        prn_info(f'Syncing desc: {desc} -> {new_desc}')
        ntp.system_cmd(f'task modify {cur_item_uuid} description:"{new_desc}"')

    # Sync Status
    if status == '-' and tw_status != 'pending':
        prn_info(f'Syncing status: {tw_status} -> pending')
        ntp.system_cmd(f'task modify {cur_item_uuid} status:pending')
    if status == '!' and tw_status != 'completed':
        prn_info(f'Syncing status: {tw_status }-> completed')
        ntp.system_cmd(f'task modify {cur_item_uuid} status:completed')
    if status == 'X' and tw_status != 'deleted':
        prn_info(f'Syncing status: {tw_status }-> deleted')
        ntp.system_cmd(f'task modify {cur_item_uuid} status:deleted')
    if status == 'A' and ('inv' not in tw_tags or 'ar' not in tw_tags):
        prn_info(f'Syncing status: archived')
        ntp.system_cmd(f'task modify {cur_item_uuid} +ar')
    if status != 'A' and ('inv' in tw_tags or 'ar' in tw_tags):
        prn_info(f'Syncing status: unarchived')
        ntp.system_cmd(f'task modify {cur_item_uuid} -ar')

    has_gcode = False
    for tag in tags.parts:
        v = list(tag.value.values())[0]
        if v == 'gcode':
            has_gcode = True

    # Sync Project and gcode
    if gcode != tw_gcode:
        prn_info('Syncing gcode')
        ntp.system_cmd(f'task modify {cur_item_uuid} gcode:{gcode}')
    if proj != tw_proj:
        prn_info('Syncing proj')
        ntp.system_cmd(f'task modify {cur_item_uuid} project:{proj}')

    # If gcode is in the note tags, add +inv +gcode. This is for a task that represents 
    # the entire project and should have its own context.
    if has_gcode and ('inv' not in tw_tags or 'gcode' not in tw_tags):
        ntp.system_cmd(f'task modify {cur_item_uuid} +inv +gcode -area -res')
    if not has_gcode and ('gcode' in tw_tags):
        ntp.system_cmd(f'task modify {cur_item_uuid} -gcode')
    if dirname != 'area' and dirname != 'resources' and not has_gcode and 'inv' in tw_tags:
        ntp.system_cmd(f'task modify {cur_item_uuid} -inv')

    if dirname != 'area' and dirname != 'resources' and ('area' in tw_tags or 'res' in tw_tags):
        ntp.system_cmd(f'task modify {cur_item_uuid} -area -res -inv -gcode')
    if dirname != 'areas' and 'area' in tw_tags:
        ntp.system_cmd(f'task modify {cur_item_uuid} -area')
    if dirname != 'resources' and 'res' in tw_tags:
        ntp.system_cmd(f'task modify {cur_item_uuid} -res')

    if not has_gcode and dirname == 'areas' and 'area' not in tw_tags:
        ntp.system_cmd(f'task modify {cur_item_uuid} +inv +area')
    if not has_gcode and dirname == 'resources' and 'res' not in tw_tags:
        ntp.system_cmd(f'task modify {cur_item_uuid} +inv +res')

    return cur_item_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    sync_task(filename, lineno)
