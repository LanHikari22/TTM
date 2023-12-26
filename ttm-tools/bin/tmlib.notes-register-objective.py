#!/bin/python3

import sys
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

prn_error = print
prn_warn = print

def register_objective(filename, lineno) -> str:
    parsed_items = ntp.process_note_file(filename)
    cur_item = ntp.find_item_at_lineno(parsed_items, lineno)

    cur_item_uuid = ntp.get_tag(cur_item, 'uuid')
    if cur_item_uuid != '':
        # We're done here, already registered
        prn_warn(f'item at lineno {lineno} is already registered with uuid {cur_item_uuid}')
        return ''

    parent_lineno, parent_item = ntp.find_parent_item(parsed_items, lineno)
    parent_item_uuid = ntp.get_tag(parent_item, 'uuid')
    if parent_item_uuid == '':
        # We also need to register the parent
        #print(f'Registering parent of {lineno} at {parent_lineno}')
        parent_item_uuid = register_objective(filename, parent_lineno)
    if parent_item_uuid == '':
        prn_error(f'error: Failed to register parent of {lineno} at {parent_lineno}')
        return ''

    cur_item_desc_part = cur_item.get_part(ntp.ItemType.KV, key='desc')
    if not cur_item_desc_part:
        prn_error(f'error: Failed to get desc of {lineno}')
        return ''
    cur_item_desc = cur_item_desc_part.value['desc']

    # Register this item as an objective against parent_item_uuid
    new_uuid = ntp.system_create_objective(parent_item_uuid)
    if new_uuid == '':
        return ''

    # Rename the description based on the current item
    new_desc = ntp.system_rename_objective(new_uuid, cur_item_desc)
    if new_desc == '':
        return ''

    # Modify the current line to reflect the new changes. 
    new_childno = new_desc.split(' ')[0].split('.')[1]
    #print('new_childno', new_childno)
    cur_item_tags = cur_item.get_part(ntp.ItemType.TAGS)
    new_tags = [ntp.Item(ntp.ItemType.KV, {'childno': new_childno}, []), ntp.Item(ntp.ItemType.KV, {'uuid': new_uuid})]
    if not cur_item_tags:
        cur_item_tags = ntp.Item(ntp.ItemType.TAGS, '', new_tags)
        cur_item.parts.append(cur_item_tags)
    else:
        for tag in new_tags:
            cur_item_tags.parts.append(tag)
    #print('modified', cur_item)
    #print('modified_built', build_objective_line_item(cur_item))

    # Inplace modify the file with the new content. The prints in this loop are directed into the file.
    for line in fileinput.input(filename, inplace=True):
        if line == cur_item.value:
            print(ntp.build_objective_line_item(cur_item) + '\n', end='')
        else:
            print(line, end='')

    return new_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    #print(f'Thank you for using vim! Your filename is {filename} and your lineno is {lineno}! Its so amazing!')
    register_objective(filename, lineno)
