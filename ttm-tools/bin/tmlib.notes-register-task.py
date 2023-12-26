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

def register_task(filename, lineno) -> str:
    parsed_items = ntp.process_note_file(filename)
    cur_item = ntp.find_item_at_lineno(parsed_items, lineno)
    cur_item_tags = cur_item.get_part(ntp.ItemType.TAGS)

    print(cur_item)

    cur_item_uuid = ntp.get_tag(cur_item, 'uuid')
    if cur_item_uuid != '':
        # Nothing to do here
        prn_info('Task is already registered')
        return ''

    print(cur_item_uuid)

    # Get the task description
    desc = cur_item.get_part(ntp.ItemType.KV, key='desc').value['desc']
    note_token = cur_item.get_part(ntp.ItemType.NOTE_TOKEN).value

    # Get the gcode and project from the notes filename
    basename = os.path.basename(filename)
    basename_split = basename.split('-')
    gcode = basename_split[0]
    proj = '-'.join(basename_split[1:])

    # If gcode is in the note tags, add +inv +gcode. This is for a task that represents 
    # the entire project and should have its own context.
    has_gcode = False
    for tag in cur_item_tags.parts:
        v = list(tag.value.values())[0]
        if v == 'gcode':
            has_gcode = True

    extra_tags = ''
    if has_gcode:
        if '+inv' not in extra_tags:
            extra_tags += '+inv '
        extra_tags += '+gcode '

    # The task may be in the projects, areas, or resources folder. These determine the tags for context. project is default visiblity.
    if basename == filename:
        prn_error('Please specify the path for whether this is in proj, areas, or resources.')
        return ''
    dirname = os.path.basename(filename.replace(basename, '')[:-1])
    #print('f', filename, 'b', basename, 'g', filename.replace(basename, '')[:-1])
    if dirname == 'areas' and not has_gcode:
        extra_tags += '+inv +area '
    if dirname == 'resources' and not has_gcode:
        extra_tags += '+inv +res '
    #print('dirname', dirname)
    #print('extra_tags', extra_tags)


    context = ntp.system_cmd("task 2>&1 | perl -wne '/Context .(.*). set.*/i and print $1' 2>/dev/null")
    if context == '':
        context = 'none'

    # Create new task
    ntp.system_cmd('task context none')
    stdout = ntp.system_cmd(f'task add +tT {extra_tags.strip()} gc:{gcode} proj:{proj} {desc}')
    ntp.system_cmd(f'task context {context}')

    # Parse out Task relative id
    new_rel_id = -1
    p = re.compile('Created task (\d+).')
    for line in stdout.split('\n'):
        m = p.match(line)
        if m:
            new_rel_id = m.groups()[0]
            break
    if new_rel_id == -1:
        prn_error('error: Could not parse relative id')
        return ''

    # Retrieve UUID from relative id
    new_uuid = ntp.system_cmd(f'task _get {new_rel_id}.uuid').split('-')[0]
    print(new_uuid)

    # Modify its notelinks
    ntp.system_cmd(f'task modify {new_uuid} notelinks:{note_token}')
    #result = subprocess.run(['task', 'modify', f'{uuid}', f'sch:today'], stdout=subprocess.PIPE)

    # Modify the current line to reflect the new changes. 
    new_tags = [ntp.Item(ntp.ItemType.KV, {'uuid': new_uuid})]
    if not cur_item_tags:
        cur_item_tags = ntp.Item(ntp.ItemType.TAGS, '', new_tags)
        cur_item.parts.append(cur_item_tags)
    else:
        for tag in new_tags:
            cur_item_tags.parts.append(tag)
    #print('modified', cur_item)
    #print('modified_built', ntp.build_note_def_line_item(cur_item))

    # Inplace modify the file with the new content. The prints in this loop are directed into the file.
    for line in fileinput.input(filename, inplace=True):
        if line == cur_item.value:
            print(ntp.build_note_def_line_item(cur_item) + '\n', end='')
        else:
            print(line, end='')


    return cur_item_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    register_task(filename, lineno)
