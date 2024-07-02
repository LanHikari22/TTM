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
import pipe

spec=importlib.util.spec_from_file_location("note_parser","/root/.local/bin/tmlib.note-parser.py")
note_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_parser)
ntp = note_parser

prn_error = print
prn_warn = print
prn_info = print


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

def process_task_notelog_entires_for_file(filename: str):
    # filename = '/root/notes/projects/TTM1-ttm_dev'
    parsed_items = ntp.process_note_file(filename, incl_logs=True)

    # print(parsed_items)
    
    task_grouped = cluster_items_by_objective(parsed_items)

    for i in range(len(task_grouped)):

        items = task_grouped[i] | pipe.map(lambda lineno_item: lineno_item[1])  \
                                | pipe.Pipe(list)

        if len(task_grouped[i]) > 1:
            first_item = items[0]
            for lineno, item in task_grouped[i][1:]:
                desc = item.get_part(ntp.ItemType.KV, key='desc').value['desc'].strip()

                # one word descriptions are usually just section names. Not very informative for us.
                if len(desc.split(' ')) < 2:
                    continue

                print(filename + ':' + str(lineno) + ':' + first_item.value.strip())
                item_val = item.value.replace('\n\n', '\n').strip()


                for line in item_val.split('\n'):
                    line = line.strip()
                    if line:
                        print(filename + ':' + str(lineno) + ':\t' + line)

                print('/ENTRY')



if __name__ == '__main__':

    directory = '/root/notes'

    import os
    from glob import glob
    filenames = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*'))]

    for filename in filenames:
        try:
            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                process_task_notelog_entires_for_file(filename)
        except Exception:
            pass
