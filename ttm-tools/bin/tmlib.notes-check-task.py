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

def check_task(filename, lineno) -> str:
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

    os.system(f'task {cur_item_uuid}')
    return cur_item_uuid

if __name__ == '__main__':
    filename = sys.argv[1]
    lineno = int(sys.argv[2])
    check_task(filename, lineno)
