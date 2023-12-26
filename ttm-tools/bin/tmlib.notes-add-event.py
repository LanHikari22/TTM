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

spec=importlib.util.spec_from_file_location("reg_objective","/root/.local/bin/tmlib.notes-register-objective.py")
reg_objective = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg_objective)
rgo = reg_objective

prn_err = print
prn_warn = print
prn_info = print

def system_calcure_add_event(uuid) -> bool:
    result = subprocess.run(['tmlib.cli-calcure-add-tw-event', uuid], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to add calcure event')
        return False

    return True

def system_set_schedule_event_to_today(uuid) -> bool:
    result = subprocess.run(['task', 'modify', f'{uuid}', f'sch:today'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to modify sch for {uuid}')
        return False

    result = subprocess.run(['task', 'modify', f'{uuid}', f'endsch:today'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to modify endsch for {uuid}')
        return False

    return True

def add_event(filename, lineno) -> str:
    parsed_items = ntp.process_note_file(filename)
    cur_item = ntp.find_item_at_lineno(parsed_items, lineno)

    # Get Item UUID and Register if necessary
    cur_item_uuid = ntp.get_tag(cur_item, 'uuid')
    if cur_item_uuid == '':
        # We need to register this item first.
        prn_info(f'item at lineno {lineno} is not registered. Registering...')
        cur_item_uuid = rgo.register_objective(filename, lineno)
    if cur_item_uuid == '':
        prn_error(f'error: Could not register item')
        return ''

    system_set_schedule_event_to_today(cur_item_uuid)
    system_calcure_add_event(cur_item_uuid)

    return cur_item_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    add_event(filename, lineno)
