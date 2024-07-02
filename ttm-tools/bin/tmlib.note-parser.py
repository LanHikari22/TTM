#!/bin/python3

import sys
import subprocess
import re
import fileinput
from enum import Enum, auto
from typing import List, Optional, Tuple

prn_error = print
prn_warn = print

class ItemType(Enum):
    # Lines
    ENTRY_DEFINITION_LINE = auto()          # (TAB_LEVEL, NOTE_TOKEN, desc: KV, TAGS(uuid: KV, ...))
    OBJECTIVE_LINE = auto()                 # (TAB_LEVEL, TIME_DATE, status: KV, desc: KV,[REF_COUNT,][USED_AS_REF,]
    LOG_LINE = auto()                       # (TAB_LEVEL, TIME_DATE, desc: KV,[REF_COUNT,][USED_AS_REF,]
                                            # [, TAGS([childno: KV,][uuid: KV,] ...)])

    # Meta information
    TAB_LEVEL = auto()

    # Tokens
    TAGS = auto()                           # ({KV ...})
    KV = auto()
    NOTE_TOKEN = auto()                     # (entry_name: KV, date_code: KV, week_num: KV, MTWRFSU: KV, rand4: KV)
    TIME_DATE = auto()                      # (date_code: KV, week_num: KV, MTWRFSU: KV, HH: KV, MM: KV)
    USED_AS_REF = auto()
    REF_COUNT = auto()                      # (n: KV)

class Item:
    def __init__(self, item_type: ItemType, value, parts: List['Item']=None):
        self.item_type = item_type
        self.value = value

        if not parts:
            self.parts = []
        else:
            self.parts = parts

    @staticmethod
    def parse(item_type: ItemType, line: str, verbose=False) -> Optional['Item']:
        RE_UUID = '[abcdef1234567890]{8}'
        RE_TAB_LEVEL = '[\s]*'
        RE_NOTE_TOKEN = 'P\[[\d]{6}-W[\d]+[MTWRFSU]-[\d]{4}\]'
        RE_NOTE_TOKEN_GRP = '(P)\[([\d]{6})-W([\d]+)([MTWRFSU])-([\d]{4})\]'
        RE_TAGS = f'\(tags:.*\)'
        RE_TAGS_GRP = f'\(tags:\s*(.*)\s*\)'
        RE_TIME_DATE = '\d{6}-W\d{2}[MTWRFSU] \d{2}:\d{2}'
        RE_TIME_DATE_GRP = '(\d{6})-W(\d{2})([MTWRFSU]) (\d{2}):(\d{2})'
        RE_USED_AS_REF = '\(Ref\)'
        RE_REF_COUNT = '\[Refs \d+\]'
        RE_REF_COUNT_GRP = '\[Refs (\d+)\]'
        RE_OBJECTIVE_STATUS = '\([-!XAB]\)'
        RE_OBJECTIVE_STATUS_GRP = '\(([-!XAB])\)'
        RE_NOTE_DEF_DESC_GRP = f'{RE_TAB_LEVEL}{RE_NOTE_TOKEN}-\s*(.*)\s*{RE_TAGS}'
        RE_OBJECTIVE_LINE_DESC_GRP = f'{RE_TAB_LEVEL}- {RE_TIME_DATE} - {RE_OBJECTIVE_STATUS}\s*(.*)'
        RE_LOG_LINE_DESC_GRP = f'{RE_TAB_LEVEL}[-_] {RE_TIME_DATE} -\s*(.*)'

        def kv(k, v):
            return Item(ItemType.KV, {k: v}, [])

        if item_type == ItemType.ENTRY_DEFINITION_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    prn_error('error: Failed to parse tab_level')
                return None

            note_token = Item.parse(ItemType.NOTE_TOKEN, line)
            if not note_token:
                if verbose:
                    prn_erro('error: Failed to parse note_token')
                return None

            # Parse Description
            p = re.compile(f'{RE_NOTE_DEF_DESC_GRP}')
            m = p.match(line)
            if not m:
                if verbose:
                    prn_error('error: note definition schema is not met')
                return None
            desc = kv('desc', m.groups()[0])

            # Parse Tags
            tags = Item.parse(ItemType.TAGS, line)
            if not tags:
                if verbose:
                    prn_error('error: Could not parse tags')
                return None

            # Process tags and find UUID tag
            found_uuid_tag = 0
            new_tag_parts = []
            p = re.compile(f'{RE_UUID}')
            for tag_part in tags.parts:
                assert tag_part.item_type == ItemType.KV
                tag = tag_part.value['tag']
                tag = tag.strip()

                m = p.match(tag)
                if not m:
                    new_tag_parts.append(tag_part)
                else:
                    new_part = kv('uuid', tag)
                    new_tag_parts.append(new_part)
                    found_uuid_tag += 1
            if found_uuid_tag == 0:
                if verbose:
                    prn_error('error: could not find uuid tag')
                    return None
            if found_uuid_tag > 1:
                if verbose:
                    prn_error('error: found multiple uuids, ambiguous.')
                    return None
            tags.parts = new_tag_parts

            return Item(item_type, line, [tab_level, note_token, desc, tags])

        elif item_type == ItemType.OBJECTIVE_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    prn_error('error: Failed to parse tab_level')
                return None

            time_date = Item.parse(ItemType.TIME_DATE, line)
            if not time_date:
                if verbose:
                    prn_error('error: Failed to parse time_date')
                return None

            # Parse Status
            p = re.compile(f'{RE_TAB_LEVEL}- {RE_TIME_DATE} - {RE_OBJECTIVE_STATUS_GRP}')
            m = p.match(line)
            if not m:
                if verbose:
                    prn_error('error: Failed to parse status')
                return None
            status = kv('status', m.groups()[0])

            # Parse optional ref usage
            used_as_ref = Item.parse(ItemType.USED_AS_REF, line)
            ref_count = Item.parse(ItemType.REF_COUNT, line)
            desc = line

            if used_as_ref is not None and ref_count is not None:
                if verbose:
                    prn_error('error: Cannot be a reference and used as one simultaneously.')
                return None

            if used_as_ref:
                desc = desc.replace('(Ref)', '').strip()

            if ref_count:
                desc = desc.replace(ref_count.value, '').strip()

            # Parse Optional Tags
            tags = Item.parse(ItemType.TAGS, line)
            if tags:
                desc = desc.replace(tags.value, '').strip()

            # Parse Description
            p = re.compile(f'{RE_OBJECTIVE_LINE_DESC_GRP}')
            m = p.match(desc)
            if not m:
                if verbose:
                    prn_error('error: objective line schema is not met')
                return None
            desc = kv('desc', m.groups()[0])

            # Process tags and find UUID tag
            if tags:
                found_uuid_tag = 0
                found_childno_tag = 0
                new_tag_parts = []
                p1 = re.compile(f'{RE_UUID}')
                p2 = re.compile(f'\.\d+') # child no
                for tag_part in tags.parts:
                    assert tag_part.item_type == ItemType.KV
                    tag = tag_part.value['tag']
                    tag = tag.strip()

                    m = p1.match(tag)
                    if not m:
                        m = p2.match(tag)
                        if not m:
                            new_tag_parts.append(tag_part)
                        else:
                            new_part = kv('childno', tag)
                            new_tag_parts.append(new_part)
                            found_childno_tag += 1
                    else:
                        new_part = kv('uuid', tag)
                        new_tag_parts.append(new_part)
                        found_uuid_tag += 1

                if found_uuid_tag > 1:
                    if verbose:
                        prn_error('error: found multiple uuids, ambiguous.')
                        return None

                if found_childno_tag > 1:
                    if verbose:
                        prn_error('error: found multiple childno tags, ambiguous.')
                        return None

                tags.parts = new_tag_parts

            parts = [tab_level, time_date, status, desc]
            if used_as_ref:
                parts.append(used_as_ref)
            if ref_count:
                parts.append(ref_count)
            if tags:
                parts.append(tags)

            return Item(item_type, line, parts)

        elif item_type == ItemType.LOG_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    prn_error('error: Failed to parse tab_level')
                return None

            time_date = Item.parse(ItemType.TIME_DATE, line)
            if not time_date:
                if verbose:
                    prn_error('error: Failed to parse time_date')
                return None

            # Parse optional ref usage
            used_as_ref = Item.parse(ItemType.USED_AS_REF, line)
            ref_count = Item.parse(ItemType.REF_COUNT, line)
            desc = line

            if used_as_ref is not None and ref_count is not None:
                if verbose:
                    prn_error('error: Cannot be a reference and used as one simultaneously.')
                return None

            if used_as_ref:
                desc = desc.replace('(Ref)', '').strip()

            if ref_count:
                desc = desc.replace(ref_count.value, '').strip()

            # Parse Optional Tags
            tags = Item.parse(ItemType.TAGS, line)
            if tags:
                desc = desc.replace(tags.value, '').strip()

            # Parse Description
            p = re.compile(f'{RE_LOG_LINE_DESC_GRP}')
            m = p.match(desc)
            if not m:
                if verbose:
                    prn_error('error: objective line schema is not met')
                return None
            _desc = m.groups()[0]
            # desc = kv('desc', m.groups()[0])

            # Include any possible multilines in Description
            _lines = desc.split('\n')
            if len(_lines) > 1:
                for _line in _lines[1:]:
                    _desc += '\n' + _line.strip()


            desc = kv('desc', _desc)

            # Process tags and find UUID tag
            if tags:
                found_uuid_tag = 0
                found_childno_tag = 0
                new_tag_parts = []
                p1 = re.compile(f'{RE_UUID}')
                for tag_part in tags.parts:
                    assert tag_part.item_type == ItemType.KV
                    tag = tag_part.value['tag']
                    tag = tag.strip()

                    m = p1.match(tag)
                    if not m:
                        new_tag_parts.append(tag_part)
                    else:
                        new_part = kv('uuid', tag)
                        new_tag_parts.append(new_part)
                        found_uuid_tag += 1

                if found_uuid_tag > 1:
                    if verbose:
                        prn_error('error: found multiple uuids, ambiguous.')
                        return None

                tags.parts = new_tag_parts

            parts = [tab_level, time_date, desc]
            if used_as_ref:
                parts.append(used_as_ref)
            if ref_count:
                parts.append(ref_count)
            if tags:
                parts.append(tags)

            return Item(item_type, line, parts)

        elif item_type == ItemType.TAGS:
            p1 = re.compile(f'^.*({RE_TAGS}).*$')
            m1 = p1.match(line)
            if not m1:
                return None

            p2 = re.compile(f'^.*{RE_TAGS_GRP}.*$')
            m2 = p2.match(line)
            if not m2:
                return None

            tag_list = m2.groups()[0]
            if '#' not in tag_list:
                return None

            tag_list = tag_list.replace('#', '')
            tag_list = tag_list.split(',')
            tag_list_kv = map(lambda s: kv('tag', s.strip()), tag_list)
            return Item(item_type, m1.groups()[0], tag_list_kv)

        elif item_type == ItemType.TAB_LEVEL:
            p = re.compile(f'^({RE_TAB_LEVEL}).*')
            m = p.match(line)
            if not m:
                return Item(item_type, 0, []) 
            return Item(item_type, m.groups()[0], []) 

        elif item_type == ItemType.KV:
            raise Exception('unparsable')
            pass

        elif item_type == ItemType.NOTE_TOKEN:
            p1 = re.compile(f'\s*({RE_NOTE_TOKEN})')
            m1 = p1.match(line)
            if not m1:
                if verbose:
                    prn_error('error: line does not match note_token')
                return None

            p2 = re.compile(f'\s*{RE_NOTE_TOKEN_GRP}')
            m2 = p2.match(line)
            if not m2 or len(m2.groups()) != 5:
                if verbose:
                    prn_error('error: could not parse note_token groups')
                return None
            arr = m2.groups()

            return Item(item_type, m1.groups()[0], 
                        [kv('entry_name', arr[0]), kv('date_code', arr[1]),
                         kv('week_num', arr[2]), kv('MTWRFSU', arr[3]),
                         kv('rand4', arr[4])])

        elif item_type == ItemType.TIME_DATE:
            p1 = re.compile(f'.*({RE_TIME_DATE})')
            m1 = p1.match(line)
            if not m1:
                if verbose:
                    prn_error('error: line does not match time_date')
                return None

            p2 = re.compile(f'.*{RE_TIME_DATE_GRP}')
            m2 = p2.match(line)
            if not m2 or len(m2.groups()) != 5:
                if verbose:
                    prn_error('error: could not parse time_date groups')
                return None
            arr = m2.groups()

            return Item(item_type, m1.groups()[0], 
                        [kv('date_code', arr[0]), kv('week_num', arr[1]),
                         kv('MTWRFSU', arr[2]), kv('HH', arr[3]),
                         kv('MM', arr[4])])

        elif item_type == ItemType.USED_AS_REF:
            p = re.compile(f'.*({RE_USED_AS_REF})')
            m = p.match(line)
            if not m:
                return None

            return Item(item_type, '', [])

        elif item_type == ItemType.REF_COUNT:
            p1 = re.compile(f'.*({RE_REF_COUNT})')
            m1 = p1.match(line)
            if not m1:
                return None

            p2 = re.compile(f'.*{RE_REF_COUNT_GRP}')
            m2 = p2.match(line)
            if not m2:
                return None

            return Item(item_type, m1.groups()[0], [kv('n', m2.groups()[0])])

        else:
            raise Exception('Unknown Item ' + item_type)

    def get_part(self, part_type: ItemType, key=None) -> 'Item':
        result = []

        for part in self.parts:
            if part.item_type == part_type:
                if key is not None and part.item_type == ItemType.KV:
                    if key in part.value.keys():
                        result.append(part)
                else:
                    result.append(part)

        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result[0]
        else:
            return result

    def __str__(self):
        part_str = []
        for part in self.parts:
            part_str.append(str(part))

        result = f'Item<{self.item_type},{self.value}>'
        for s in part_str:
            result += '\n\t' + s.replace('\n', '\n\t')
        return result

def process_note_file(filename, incl_logs=False) -> List[Tuple[int, Item]]:
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    parsed_lines = []
    for i, line in enumerate(lines):
        item = Item.parse(ItemType.ENTRY_DEFINITION_LINE, line)
        if item:
            parsed_lines.append((i+1, item))
            continue

        item = Item.parse(ItemType.OBJECTIVE_LINE, line)
        if item:
            parsed_lines.append((i+1, item))
            continue

        if incl_logs:
            item = Item.parse(ItemType.LOG_LINE, line)
            if item:
                parsed_lines.append((i+1, item))
                continue

            # It is possible that the current line is a multiline continuation of the last line.
            if len(parsed_lines) > 0:
                cur_tab_level = len(Item.parse(ItemType.TAB_LEVEL, line).value) + 1 # +1: margin, missing space between '-' and the desc.

                # We want to measure the amount of characters until we begin the description. We take as referece only the first line, hence
                # value.split('\n')[0]. This is also because otherwise, it would could a whole lot of padding spaces we filter out.
                expected_tab_level = len(parsed_lines[-1][1].value.split('\n')[0]) \
                                   - len(parsed_lines[-1][1].get_part(ItemType.KV, key='desc').value['desc'])

                if parsed_lines[-1][1].item_type in [ItemType.LOG_LINE] and \
                   cur_tab_level >= expected_tab_level:
                    prev_lines = parsed_lines[-1][1].value
                    combined_lines = prev_lines + '\n' + line

                    # Let's reparse the last element.
                    item = Item.parse(ItemType.LOG_LINE, combined_lines)
                    if item:
                        parsed_lines[-1] = (parsed_lines[-1][0], item)

    return parsed_lines

def find_item_at_lineno(parsed_items: List[Tuple[int, Item]], lineno: int) -> Item:
    for i, item in parsed_items:
        if lineno == i:
            return item
    return None
        
def find_parent_item(parsed_items: List[Tuple[int, Item]], lineno: int) -> Optional[Tuple[int, Item]]:
    reversed_parsed_items = list(reversed(parsed_items))

    start_looking_for_parent = False
    current_tab_level = 0
    for i, item in reversed_parsed_items:
        if start_looking_for_parent:
            tab_level = len(item.get_part(ItemType.TAB_LEVEL).value)
            if tab_level < current_tab_level:
                return (i, item)
        else:
            if item.item_type not in [ItemType.ENTRY_DEFINITION_LINE, ItemType.OBJECTIVE_LINE]:
                raise Exception('Root-level items must be lines')

            if lineno == i:
                current_tab_level = len(item.get_part(ItemType.TAB_LEVEL).value)
                start_looking_for_parent = True
    return None

def get_tag(item: Item, key) -> str:
    tags = item.get_part(ItemType.TAGS)
    if tags:
        kv = tags.get_part(ItemType.KV, key=key)
        if kv:
            return kv.value[key]
    return ''

def system_create_objective(uuid) -> str:
    result = subprocess.run(['tmlib.cli-vit-new-objective', uuid], stdout=subprocess.PIPE)

    if result.returncode != 0:
        prn_error(f'error: Failed to create objective for {uuid}')
        return ''
    
    # Parse new UUID from stdout
    new_uuid = ''
    stdout = result.stdout.decode('ascii')
    stdout_lines = stdout.split('\n')
    re_s = '.*Created new objective ([abcdef1234567890]{8}) for ' + uuid
    #print(re_s)
    p = re.compile(re_s)
    for line in stdout_lines:
        m = p.match(str(result.stdout))
        if m:
            new_uuid = m.groups()[0]
    if new_uuid == '':
        prn_error('error: Failed to parse new uuid for created objective')
        return ''

    return new_uuid

def system_rename_objective(uuid, desc) -> str:
    result = subprocess.run(['task', '_get', f'{uuid}.description'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to get description of {uuid}')
        return ''
    stdout = result.stdout.decode('ascii')

    # keep the first portion as it indicates this is an objective
    p = re.compile('^([abcdef1234567890]{8}\.\d+).*')
    m = p.match(stdout)
    if not m:
        prn_error('error: Failed to find parent uuid in desc')
        return ''
    new_desc = m.groups()[0] + ' ' + desc
    #print(desc, '->', new_desc)
    
    result = subprocess.run(['task', 'modify', f'{uuid}', f'description:{new_desc}'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        prn_error(f'error: Failed to modify description for {uuid}')
        return ''
    return new_desc

def build_objective_line_item(item: Item) -> str:
    tab_level = item.get_part(ItemType.TAB_LEVEL)
    if not tab_level:
        return ''
    tab_level = tab_level.value

    time_date = item.get_part(ItemType.TIME_DATE)
    if not time_date:
        return ''
    date_code = time_date.get_part(ItemType.KV, key='date_code').value['date_code']
    week_num = time_date.get_part(ItemType.KV, key='week_num').value['week_num']
    MTWRFSU = time_date.get_part(ItemType.KV, key='MTWRFSU').value['MTWRFSU']
    HH = time_date.get_part(ItemType.KV, key='HH').value['HH']
    MM = time_date.get_part(ItemType.KV, key='MM').value['MM']
    status = time_date.get_part(ItemType.KV, key='MM').value['MM']

    status = item.get_part(ItemType.KV, key='status').value['status']
    desc = item.get_part(ItemType.KV, key='desc').value['desc'].strip()

    result = f'{tab_level}- {date_code}-W{week_num}{MTWRFSU} {HH}:{MM} - ({status}) {desc}'

    # Optional: Used as Ref
    used_as_ref = item.get_part(ItemType.USED_AS_REF)
    if used_as_ref:
        result += ' (Ref)'

    # Optional: Ref Count
    ref_count = item.get_part(ItemType.REF_COUNT)
    if ref_count:
        n = ref_count.get_part(ItemType.KV, key='n').value['n']
        result += f' [Refs {n}]'

    # Optional: Tags
    tags = item.get_part(ItemType.TAGS)
    if tags:
        tag_list = []
        for part in tags.parts:
            if 'childno' in part.value.keys():
                tag = '.' + list(part.value.values())[0]
            else:
                tag = list(part.value.values())[0]

            tag_list.append(tag)

        result += ' (tags: '
        for tag in tag_list:
            if tag == '':
                continue
            result += f'#{tag}, '
        result += ')'

    return result

def build_note_def_line_item(item: Item) -> str:
    tab_level = item.get_part(ItemType.TAB_LEVEL)
    if not tab_level:
        return ''
    tab_level = tab_level.value

    note_token = item.get_part(ItemType.NOTE_TOKEN)
    if not note_token:
        return ''
    entry_name = note_token.get_part(ItemType.KV, key='entry_name').value['entry_name']
    date_code = note_token.get_part(ItemType.KV, key='date_code').value['date_code']
    week_num = note_token.get_part(ItemType.KV, key='week_num').value['week_num']
    MTWRFSU = note_token.get_part(ItemType.KV, key='MTWRFSU').value['MTWRFSU']
    rand4 = note_token.get_part(ItemType.KV, key='rand4').value['rand4']

    desc = item.get_part(ItemType.KV, key='desc').value['desc'].strip()

    tags = item.get_part(ItemType.TAGS)
    if not tags:
        return ''

    tag_list = []
    for part in tags.parts:
        tag = list(part.value.values())[0]
        tag_list.append(tag)

    result = f'{tab_level}{entry_name}[{date_code}-W{week_num}{MTWRFSU}-{rand4}]- {desc}'

    result += ' (tags: '
    for tag in tag_list:
        if tag == '':
            continue
        result += f'#{tag}, '
    result += ')'

    return result

def system_cmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    stdout = output.decode().strip()
    return stdout

