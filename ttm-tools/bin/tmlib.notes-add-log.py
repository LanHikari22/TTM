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

prn_error = print
prn_warn = print
prn_info = print


def system_calcure_add_event(uuid) -> bool:
    result = subprocess.run(['tmlib.cli-calcure-add-tw-event', uuid, 'unimportant'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to add calcure event')
        return False

    return True


def get_rounded_time_now():
    from datetime import datetime
    import math

    now = datetime.now()
    rounded_minutes = math.ceil(now.minute / 5) * 5
    hour = now.hour

    # Adjust for any rounding that pushes to the next hour
    if rounded_minutes == 60:
        rounded_minutes = 0
        hour = (hour + 1) % 24

    return hour, rounded_minutes


def system_set_schedule_event_to_today(uuid) -> bool:
    # When adding an event, let's just assume it's added for now. Rounded to 5 minutes.
    hh, mm = get_rounded_time_now()

    result = subprocess.run(['task', 'modify', f'{uuid}', f'sch:today+{hh}h+{mm}min'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to modify sch for {uuid}')
        return False

    result = subprocess.run(['task', 'modify', f'{uuid}', f'endsch:today'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to modify endsch for {uuid}')
        return False

    return True


def get_uuid_from_expected_csv(filename: str, lineno: int) -> Optional[str]:
    with open(filename, 'r') as fr:
        lines = fr.readlines()

    for i, line in enumerate(lines):
        if lineno != i+1:
            continue
        
        # Don't care about tabbing or anything for this
        line = line.strip()

        expected_fields = ['status', 'yyyy', 'mm', 'dd', 'weekcode', 'interval', 'scope', 'color', 'type', 'priority', 
                           'gcode', 'uuid', 'proj', 'desc']

        tokens = line.split(',')

        if len(tokens) < len(expected_fields):
            raise Exception(f'line does not match expected format: {line}')

        return tokens[expected_fields.index('uuid')]


def get_uuid_from_events_csv(filename: str, lineno: int) -> Optional[str]:
    with open(filename, 'r') as fr:
        lines = fr.readlines()

    for i, line in enumerate(lines):
        if lineno != i+1:
            continue
        
        # Don't care about tabbing or anything for this
        line = line.strip()

        expected_fields = ['id', 'yyyy', 'mm', 'dd', 'desc', 'repeat', 'repeat1', 'status']
        expected_desc_fields = ['interval', 'type', 'gcode', 'uuid', 'proj', 'desc']

        tokens = line.split(',')

        if len(tokens) < len(expected_fields):
            raise Exception(f'line does not match expected format: {line}')

        tokens = tokens[expected_fields.index('desc')].split(' ')

        if len(tokens) < len(expected_desc_fields):
            raise Exception(f'line does not match expected format for desc: {line}')

        return tokens[expected_desc_fields.index('uuid')]


def add_event(filename, lineno) -> str:
    if 'expected.csv' in filename:
        cur_item_uuid = get_uuid_from_expected_csv(filename, lineno)
    elif 'events.csv' in filename:
        cur_item_uuid = get_uuid_from_events_csv(filename, lineno)
    else:
        # Assume this is a notelog file format
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
