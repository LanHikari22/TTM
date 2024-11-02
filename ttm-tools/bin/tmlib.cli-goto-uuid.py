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


def system_goto_uuid(uuid) -> bool:
    # os.system(f'tmlib.cli-goto-uuid {uuid}')
    result = subprocess.run(['tmlib.cli-goto-uuid', uuid], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to add calcure event')
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


def process(filename, lineno) -> str:
    if 'expected.csv' in filename:
        cur_item_uuid = get_uuid_from_expected_csv(filename, lineno)
    elif 'events.csv' in filename:
        cur_item_uuid = get_uuid_from_events_csv(filename, lineno)
    else:
        # Assume this is a notelog file format
        parsed_items = ntp.process_note_file(filename, incl_refs=True)
        cur_item = ntp.find_item_at_lineno(parsed_items, lineno)
        print('ITEM', cur_item)

        # Get Item UUID 
        cur_item_uuid = ntp.get_kv(cur_item, 'uuid')
        if cur_item_uuid == '':
            prn_err(f'Could not find uuid tag for {cur_item_uuid}')
            exit(1)

    system_goto_uuid(cur_item_uuid)

    return cur_item_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    process(filename, lineno)
