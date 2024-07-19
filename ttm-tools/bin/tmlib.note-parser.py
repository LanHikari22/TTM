#!/bin/python3

import sys
import subprocess
import re
import fileinput
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
import pipe
import argparse
import datetime
import unittest

log_file = '/tmp/note-parser.log'
verbose = 2
log_echo_stdout = False

def log_any(s, status, verbose_level):
    from datetime import datetime as dtdt

    if verbose < verbose_level:
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


class ItemType(Enum):
    # Lines
    ENTRY_DEFINITION_LINE = auto()          # (TAB_LEVEL, NOTE_TOKEN, desc: KV, TAGS(uuid: KV, ...))
    OBJECTIVE_LINE = auto()                 # (TAB_LEVEL, TIME_DATE, status: KV, desc: KV,[REF_COUNT,][USED_AS_REF,]
                                            # [, TAGS([childno: KV,][uuid: KV,] ...)])
    LOG_LINE = auto()                       # (TAB_LEVEL, TIME_DATE, desc: KV,[REF_COUNT,][USED_AS_REF,]
    CITATION_LINE = auto()                  # (TAB_LEVEL, TIME_DATE, node: KV, desc: KV[, uuid: KV], relations: {CITE_RELATION ...})

    # Meta information
    TAB_LEVEL = auto()

    # Tokens
    TAGS = auto()                           # ({KV ...})
    KV = auto()
    NOTE_TOKEN = auto()                     # (entry_name: KV, date_code: KV, week_num: KV, MTWRFSU: KV, rand4: KV)
    TIME_DATE = auto()                      # (date_code: KV, week_num: KV, MTWRFSU: KV, HH: KV, MM: KV)
    USED_AS_REF = auto()
    REF_COUNT = auto()                      # (n: KV)
    CITE_RELATION = auto()                  # (node: KV, relation: KV, is_from: KV[, status: KV])
    CITE_CODE = auto()                     # ({code: KV[, n: KV] ...})

class Item:
    def __init__(self, item_type: ItemType, value, parts: List['Item']=None):
        self.item_type = item_type
        self.value = value

        if not parts:
            self.parts = []
        else:
            self.parts = parts

    @staticmethod
    def parse_whole_and_groups(line, regex_whole, regex_groups):
        # .*? is a non-greeding everything before.
        p1 = re.compile(f'.*?({regex_whole})')
        m1 = p1.match(line)
        if not m1:
            return -1, None, None
        whole_box = m1.groups()[0]

        # log_debug(f'whole_box: {whole_box}, line: {line}')

        p2 = re.compile(f'.*?{regex_groups}')
        m2 = p2.match(whole_box)
        if not m2:
            return -2, None, None
        
        return (0, whole_box, m2.groups())

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
        RE_CITE_RELATION_FROM = r'/[^\s]*::[^\s]*?/'
        RE_CITE_RELATION_FROM_GRP = r'/([^\s]*?)::([^\s]*?)/'
        RE_CITE_RELATION_TO = r'\\[^\s]*?::[^\s]*?\\'
        RE_CITE_RELATION_TO_GRP = r'\\([^\s]*?)::([^\s]*?)\\'
        RE_CITE_CODE_GRP = r'\[\^([^\]]+)\]'
        RE_CITE_CODE = r'\[\^.*?\]'
        RE_NOTE_DEF_DESC_GRP = f'{RE_TAB_LEVEL}{RE_NOTE_TOKEN}-\s*(.*)\s*{RE_TAGS}'
        RE_OBJECTIVE_LINE_DESC_GRP = f'{RE_TAB_LEVEL}- {RE_TIME_DATE} - {RE_OBJECTIVE_STATUS}\s*(.*)'
        RE_LOG_LINE_DESC_GRP = f'{RE_TAB_LEVEL}[-_] {RE_TIME_DATE} -\s*(.*)'

        cls = Item

        def kv(k, v):
            """
            Creates a KV Item
            """
            return Item(ItemType.KV, {k: v}, [])

        if item_type == ItemType.ENTRY_DEFINITION_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    log_error('Failed to parse tab_level')
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
                    log_error('Note definition schema is not met')
                return None
            desc = kv('desc', m.groups()[0])

            # Parse Tags
            tags = Item.parse(ItemType.TAGS, line)
            if not tags:
                if verbose:
                    log_error('Could not parse tags')
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
                    log_error('Could not find uuid tag')
                    return None
            if found_uuid_tag > 1:
                if verbose:
                    log_error('Found multiple uuids, ambiguous.')
                    return None
            tags.parts = new_tag_parts

            return Item(item_type, line, [tab_level, note_token, desc, tags])

        elif item_type == ItemType.OBJECTIVE_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    log_error('Failed to parse tab_level')
                return None

            time_date = Item.parse(ItemType.TIME_DATE, line)
            if not time_date:
                if verbose:
                    log_error('Failed to parse time_date')
                return None

            # Parse Status
            p = re.compile(f'{RE_TAB_LEVEL}- {RE_TIME_DATE} - {RE_OBJECTIVE_STATUS_GRP}')
            m = p.match(line)
            if not m:
                if verbose:
                    log_error('Failed to parse status')
                return None
            status = kv('status', m.groups()[0])

            # Parse optional ref usage
            used_as_ref = Item.parse(ItemType.USED_AS_REF, line)
            ref_count = Item.parse(ItemType.REF_COUNT, line)
            desc = line

            if used_as_ref is not None and ref_count is not None:
                if verbose:
                    log_error('Cannot be a reference and used as one simultaneously.')
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
                    log_error('objective line schema is not met')
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
                        log_error('Found multiple uuids, ambiguous.')
                        return None

                if found_childno_tag > 1:
                    if verbose:
                        log_error('Found multiple childno tags, ambiguous.')
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
                    log_error('Failed to parse tab_level')
                return None

            time_date = Item.parse(ItemType.TIME_DATE, line)
            if not time_date:
                if verbose:
                    log_error('Failed to parse time_date')
                return None

            # Parse optional ref usage
            used_as_ref = Item.parse(ItemType.USED_AS_REF, line)
            ref_count = Item.parse(ItemType.REF_COUNT, line)
            desc = line

            if used_as_ref is not None and ref_count is not None:
                if verbose:
                    log_error('Cannot be a reference and used as one simultaneously.')
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
                    log_error('Objective line schema is not met')
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
                        log_error('Found multiple uuids, ambiguous.')
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

        elif item_type == ItemType.CITATION_LINE:
            tab_level = Item.parse(ItemType.TAB_LEVEL, line)
            if not tab_level:
                if verbose:
                    log_error('Failed to parse tab_level')
                return None

            time_date = Item.parse(ItemType.TIME_DATE, line)
            if not time_date:
                if verbose:
                    log_error('Failed to parse time_date')
                return None

            # Parse optional ref usage
            used_as_ref = Item.parse(ItemType.USED_AS_REF, line)
            ref_count = Item.parse(ItemType.REF_COUNT, line)
            desc = line

            if used_as_ref is not None and ref_count is not None:
                if verbose:
                    log_error('Cannot be a reference and used as one simultaneously.')
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
                    log_error('Objective line schema is not met')
                return None
            _desc = m.groups()[0]
            # desc = kv('desc', m.groups()[0])

            # Include any possible multilines in Description
            _lines = desc.split('\n')
            if len(_lines) > 1:
                for _line in _lines[1:]:
                    _desc += '\n' + _line.strip()
            
            # Let's parse the cite code for this citation
            cite_code = Item.parse(ItemType.CITE_CODE, _desc)
            if not cite_code or cite_code.value + ':' not in _desc:
                if verbose:
                    log_error('Failed to parse cite_code')
                return None

            # The description must begin with the citation code and a ': ' to be valid.
            if not _desc.startswith(cite_code.value + ': '):
                if verbose:
                    log_error('Did not start with citation code')
                return None

            _desc = _desc.replace(cite_code.value + ':', '')
            _desc = ''.join(reversed(''.join(reversed(_desc)).strip())).strip()

            # Let's parse the UUID if one exists.
            part_regex = f'#{RE_UUID}'
            part_regex_grp = f'#({RE_UUID})'
            ec, whole_str, groups = cls.parse_whole_and_groups(_desc, part_regex, part_regex_grp)
            uuid = ''
            if ec == 0 and len(groups) == 1:
                uuid = groups[0]

                # Now remove it from the description.
                _desc = _desc.replace(whole_str, '')

            # Now let's process any relations left in the description and remove them.

            # This doesn't deal well with new lines. Let's temporarily remove them.
            _desc = _desc.replace('\n','_NEWWLINEE_')

            # Keep looking for relations and remove them as you go
            relations = []
            while True:
                relation = Item.parse(ItemType.CITE_RELATION, _desc, verbose)
                if relation:
                    relations.append(relation)
                else:
                    break
                _desc = _desc.replace(relation.value, '')

            _desc = _desc.replace('_NEWWLINEE_', '\n')

            desc = kv('desc', _desc.strip())

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
                        log_error('Found multiple uuids, ambiguous.')
                        return None

                tags.parts = new_tag_parts

            parts = [tab_level, time_date, cite_code, desc]
            parts.extend(relations)

            if uuid != '':
                parts.append(kv('uuid', uuid))

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

        elif item_type == ItemType.NOTE_TOKEN:
            p1 = re.compile(f'\s*({RE_NOTE_TOKEN})')
            m1 = p1.match(line)
            if not m1:
                if verbose:
                    log_error('Line does not match note_token')
                return None

            p2 = re.compile(f'\s*{RE_NOTE_TOKEN_GRP}')
            m2 = p2.match(line)
            if not m2 or len(m2.groups()) != 5:
                if verbose:
                    log_error('Could not parse note_token groups')
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
                    log_error('Line does not match time_date')
                return None

            p2 = re.compile(f'.*{RE_TIME_DATE_GRP}')
            m2 = p2.match(line)
            if not m2 or len(m2.groups()) != 5:
                if verbose:
                    log_error('Could not parse time_date groups')
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

        elif item_type == ItemType.CITE_RELATION:
            def parse_cite_relation(line, is_from: bool):
                if is_from:
                    cite_relation_regex = RE_CITE_RELATION_FROM
                    cite_relation_grp_regex = RE_CITE_RELATION_FROM_GRP
                else:
                    cite_relation_regex = RE_CITE_RELATION_TO
                    cite_relation_grp_regex = RE_CITE_RELATION_TO_GRP

                # log_debug(f'CITE_RELATION: line: {line}')

                ec, whole_str, groups = cls.parse_whole_and_groups(line, cite_relation_regex, cite_relation_grp_regex)
                if ec == -1:
                    if is_from:
                        return parse_cite_relation(line, is_from=False)
                    return None
                elif ec == -2 or len(groups) != 2:
                    if verbose:
                        log_error('Could not parse cite_relation groups')
                    return None
                arr = groups
                # log_debug(f'arr: {arr}')

                # Do not parse past the identified area of interest
                line_area = line[:line.index(whole_str) + len(whole_str)]
                # log_debug(f'line: {line}')
                # log_debug(f'line_area: {line_area}')

                # Parse Status (optional)
                p3 = re.compile(f'.*?({RE_OBJECTIVE_STATUS} {cite_relation_regex})')
                m3 = p3.match(line_area)
                if m3:
                    whole_str = m3.groups()[0]

                status = None
                if m3:
                    p4 = re.compile(f' *{RE_OBJECTIVE_STATUS_GRP}')
                    m4 = p4.match(whole_str)
                    if m4:
                        status = kv('status', m4.groups()[0])
                
                node_idx = 0 if is_from else 1
                relation_idx = 1 if is_from else 0

                items = [kv('node', arr[node_idx]),
                        kv('relation', arr[relation_idx]),
                        kv('is_from', f'{is_from}')]

                if status:
                    items.append(status)

                result = Item(item_type, whole_str, items)

                # log_debug(f'CITE_RELATION: result: {result}')

                return result
            return parse_cite_relation(line, is_from=True)

        elif item_type == ItemType.CITE_CODE:
            ec, whole_str, groups = cls.parse_whole_and_groups(line, RE_CITE_CODE, RE_CITE_CODE_GRP)
            if ec < 0:
                return None
            groups = groups[0].split('::')
            # log_debug(f'whole_str: {whole_str}, groups: {groups}')
            full_item_str = whole_str

            codes = []
            ns = []

            # Go through each code and separate into category and number or '' if no number
            for code in groups:
                if code == None or code == '':
                    continue

                # first try to parse variable names for n, if it is not valid, we parse with/without nums
                part_regex = r'[a-zA-Z]*#.+'
                part_regex_grp = r'([a-zA-Z]*)#(.+)'
                ec, whole_str, groups = cls.parse_whole_and_groups(code, part_regex, part_regex_grp)
                valid = ec
                if ec == 0:
                    codes.append(groups[0])
                    ns.append('#' + groups[1])
                    continue

                part_regex = r'[a-zA-Z]*[\d.]+'
                part_regex_grp = r'([a-zA-Z]*)([\d.]+)'
                ec, whole_str, groups = cls.parse_whole_and_groups(code, part_regex, part_regex_grp)
                # log_debug(f'code: {code}, whole_str: {whole_str}, groups: {groups}')

                valid = ec
                if ec == 0 and groups[1].count('.') > 1:
                    if verbose:
                        log_error('Number cannot have more than one .')
                    valid = -3

                if valid == 0:
                    codes.append(groups[0])
                    ns.append(groups[1])
                else:
                    codes.append(code)
                    ns.append('')

            codes_kvs = codes | pipe.map(lambda s: kv('code', s)) | pipe.Pipe(list)
            ns_kvs = ns | pipe.map(lambda s: kv('n', s)) | pipe.Pipe(list)

            return Item(item_type, full_item_str, codes_kvs + ns_kvs)

        else:
            raise Exception('Unknown Item ' + item_type)

    def get_part(self, part_type: ItemType, key=None) -> Optional['Item']:
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

def get_kv(part, key):
    """
    Extracts the property `key` in `part` if it has a KV with that key.
    """
    kv_part = part.get_part(ItemType.KV, key=key)
    if not kv_part:
        return None

    if type(kv_part) is list:
        result = kv_part | pipe.map(lambda part: part.value[key]) | pipe.Pipe(list)
        return result

    return kv_part.value[key]

def process_note_file_lines(lines, incl_logs=False, incl_refs=False) -> List[Tuple[int, Item]]:
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

        def process_multiline(parsed_lines, line, item_type):
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
                    item = Item.parse(item_type, combined_lines)
                    if item:
                        parsed_lines[-1] = (parsed_lines[-1][0], item)


        if incl_refs:
            item = Item.parse(ItemType.CITATION_LINE, line)
            if item:
                parsed_lines.append((i+1, item))
                continue
            else:
                if incl_logs:
                    item = Item.parse(ItemType.LOG_LINE, line)
                    if item:
                        parsed_lines.append((i+1, item))
                        continue

                    process_multiline(parsed_lines, line, ItemType.LOG_LINE)

            process_multiline(parsed_lines, line, ItemType.CITATION_LINE)

        elif incl_logs:
            item = Item.parse(ItemType.LOG_LINE, line)
            if item:
                parsed_lines.append((i+1, item))
                continue

            process_multiline(parsed_lines, line, ItemType.LOG_LINE)

    return parsed_lines

def process_note_file(filename, incl_logs=False, incl_refs=False) -> List[Tuple[int, Item]]:
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    return process_note_file_lines(lines, incl_logs, incl_refs)
    
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

def find_parent_branch_items(parsed_items: List[Tuple[int, Item]], lineno: int) -> Optional[List[Tuple[int, Item]]]:
    branch = []

    while True:
        opt_lineno_item = find_parent_item(parsed_items, lineno)
        if opt_lineno_item:
            branch.append((opt_lineno_item[0], opt_lineno_item[1]))
            lineno = opt_lineno_item[0]
        else:
            break
    
    return branch


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
        log_error(f'Failed to create objective for {uuid}')
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
        log_error('Failed to parse new uuid for created objective')
        return ''

    return new_uuid

def system_rename_objective(uuid, desc) -> str:
    result = subprocess.run(['task', '_get', f'{uuid}.description'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        log_error(f'Failed to get description of {uuid}')
        return ''
    stdout = result.stdout.decode('ascii')

    # keep the first portion as it indicates this is an objective
    p = re.compile('^([abcdef1234567890]{8}\.\d+).*')
    m = p.match(stdout)
    if not m:
        log_error('Failed to find parent uuid in desc')
        return ''
    new_desc = m.groups()[0] + ' ' + desc
    #print(desc, '->', new_desc)
    
    result = subprocess.run(['task', 'modify', f'{uuid}', f'description:{new_desc}'], stdout=subprocess.PIPE)
    if result.returncode != 0:
        log_error(f'Failed to modify description for {uuid}')
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
                if tag.startswith('..'):
                    # Not sure exactly why we add an extra '.', it may be the logical built
                    # representation is consistent with the parsed one. But in case of modifying
                    # a current line tags, we already have the . added.
                    tag = tag[1:]
                            
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

def main(args: argparse.Namespace):
    print(args)

    if args.subcommand == 'iso':
        print('iso!', args.week_date)
    if args.subcommand == 'of':
        print('of!', args.date)
    if args.subcommand == 'today':
        today = datetime.date.today()
        print(today)


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help="Increase verbosity level (use -v, -vv, or -vvv)")
                   
    subparsers = p.add_subparsers(dest='subcommand')
    subparsers.required = True

    sp = subparsers.add_parser('unittest', 
                    help='run the unit tests instead of main')

    return(p.parse_args())

def _main():
    if sys.version_info<(3,5,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)

    # if you have unittest as part of the script, you can forward to it this way
    if len(sys.argv) >= 2 and sys.argv[1] == 'unittest':
        import unittest
        sys.argv[0] += ' unittest'
        sys.argv.remove('unittest')
        log_debug('Running Unit Tests')
        # log_debug(str(sys.argv))
        unittest.main()
        exit(0)

    args = cmdline_args()
    main(args)

class UnitTests(unittest.TestCase):
    # Parsing Notelog
    def test_can_parse_normal_note_log(self):
        test_lines = [
            '               - 240624-W26U 18:52 - We need to have three variations. Lets say triggered by !C, !c, and #C. One greps the tuple (task, citation), the second',
            '                                     greps the tuple (task, context, citation), and the third greps (task, notelog)',
            '                                     The first ensures uniqueness of (task, citation).',
        ]

        # This will get us a list of tuples of linenos and items.
        result = process_note_file_lines(test_lines, incl_logs=True)


        # Just immediately display it for quick debugging
        # items_str = result | pipe.map(lambda lineno_item: lineno_item[1]) \
        #                    | pipe.map(lambda item: str(item)) \
        #                    | pipe.Pipe(list)
        # for item_str in items_str:
        #     log_debug(item_str)

        self.assertTrue(len(result) == 1, 'Expected there to only be one notelog parsed.')
        lineno, item = result[0]

        self.assertEqual(lineno, 1, 'Expected that the linenumber would be 1 since it is first line.')

        tab_level = item.get_part(ItemType.TAB_LEVEL).value
        self.assertEqual(tab_level, '               ')

        time_date = item.get_part(ItemType.TIME_DATE)
        self.assertEqual(time_date.value, '240624-W26U 18:52')
        self.assertEqual(get_kv(time_date, 'date_code'), '240624')
        self.assertEqual(get_kv(time_date, 'week_num'), '26')
        self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'U')
        self.assertEqual(get_kv(time_date, 'HH'), '18')
        self.assertEqual(get_kv(time_date, 'MM'), '52')

        desc = get_kv(item, 'desc')
        self.assertTrue(desc.startswith('We need to have three variations.'))
        self.assertTrue(desc.endswith('(task, citation).'))

    # Parsing Citation Relations
    def test_can_parse_citation_relations(self):
        test_lines_dict = {
            # G0: Group of passing examples that are simple, ie the entire input is the item value
            'G0.0': '/T::cites/',
            'G0.1': '/T::milestone_of/',
            'G0.2': '(-) /T::blocks/',
            'G0.3': '(!) /T::blocks/',
            'G0.4': '/[^ATH1]::author_of/',
            'G0.5': '\\has_milestone::T\\',

            # G1: Group of passing examples that aren't simple, ie only part of the input is the item value
            'G1.0': '/T::is_self/ AAA BBB CCC/DDD',
            'G1.1': '/T::is_self/ TaskGraph::MSTN: Able to render graph representation of tasks/citations',

            # G2: False examples, although they parse. Treat this as warning.
            'G2.0': '/T::cites/ /T::blocks/',
        }

        for test_no in test_lines_dict:
            test_line = test_lines_dict[test_no]

            item = Item.parse(ItemType.CITE_RELATION, test_line)

            # Just immediately display it for quick debugging
            item_str = str(item) 
            # log_debug(f'citation_relations: test input: {test_no}: {test_line}')
            # log_debug(item_str)

            self.assertTrue(item != None, f'Failed to parse example {test_no}')

            # For group G0, The test line is itself the expected citation entity to be parsed
            if test_no.startswith('G0'):
                self.assertEqual(item.value, test_line)
            
            if test_line == '/T::cites/':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'cites')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)

            if test_line == '/T::milestone_of/':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'milestone_of')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)

            if test_line == '(-) /T::blocks/':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'blocks')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), '-')

            if test_line == '(!) /T::blocks/':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'blocks')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), '!')

            if test_line == '/[^ATH1]::author_of/':
                self.assertEqual(get_kv(item, 'node'), '[^ATH1]')
                self.assertEqual(get_kv(item, 'relation'), 'author_of')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)

            if test_line == '\\has_milestone::T\\':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'has_milestone')
                self.assertEqual(get_kv(item, 'is_from'), 'False')
                self.assertEqual(get_kv(item, 'status'), None)

            # Group G1, The item.value cannot be inferred to be automatically the test line.
            if test_line == '/T::is_self/ AAA BBB CCC/DDD':
                self.assertEqual(item.value, '/T::is_self/')
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'is_self')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)

            # 'G1.1': '/T::is_self/ TaskGraph::MSTN: Able to render graph representation of tasks/citations',
            if test_no == 'G1.1':
                self.assertEqual(item.value, '/T::is_self/')
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'is_self')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)
            
            # Group G2, False Examples but they parse. Ie these are false positives. Be warned.

            # Algorithm cannot handle the existence of multiple entities. Gives only first.
            if test_line == '/T::cites/ /T::blocks/':
                self.assertEqual(get_kv(item, 'node'), 'T')
                self.assertEqual(get_kv(item, 'relation'), 'cites')
                self.assertEqual(get_kv(item, 'is_from'), 'True')
                self.assertEqual(get_kv(item, 'status'), None)

    def test_can_parse_cite_codes(self):
        test_lines = [
            '[^ATH1]',
            '[^ATH3]',
            '[^T30]',
            '[^PRJ::T2]',
            '[^P::GH1::GHI1]',
            '[^TL3.5]',
            '[^FL#variable_name]',
            '[^FL#file55]',

            '[^TL3..5]',            # False example
        ]

        for test_line in test_lines:
            item = Item.parse(ItemType.CITE_CODE, test_line)
            self.assertTrue(item != None)

            # Just immediately display it for quick debugging
            item_str = str(item) 
            # log_debug(f'test_line: {test_line}')
            # log_debug(item_str)

            self.assertEqual(item.value, test_line)

            if test_line == '[^ATH1]':
                self.assertEqual(get_kv(item, 'code'), 'ATH')
                self.assertEqual(get_kv(item, 'n'), '1')

            if test_line == '[^ATH3]':
                self.assertEqual(get_kv(item, 'code'), 'ATH')
                self.assertEqual(get_kv(item, 'n'), '3')

            if test_line == '[^T30]':
                self.assertEqual(get_kv(item, 'code'), 'T')
                self.assertEqual(get_kv(item, 'n'), '30')

            if test_line == '[^PRJ::T2]':
                self.assertEqual(get_kv(item, 'code'), ['PRJ', 'T'])
                self.assertEqual(get_kv(item, 'n'), ['', '2'])

            if test_line == '[^P::GH1::GHI1]':
                self.assertEqual(get_kv(item, 'code'), ['P', 'GH', 'GHI'])
                self.assertEqual(get_kv(item, 'n'), ['', '1', '1'])

            if test_line == '[^TL3.5]':
                self.assertEqual(get_kv(item, 'code'), 'TL')
                self.assertEqual(get_kv(item, 'n'), '3.5')

            if test_line == '[^FL#variable_name]':
                self.assertEqual(get_kv(item, 'code'), 'FL')
                self.assertEqual(get_kv(item, 'n'), '#variable_name')

            if test_line == '[^FL#file55]':
                self.assertEqual(get_kv(item, 'code'), 'FL')
                self.assertEqual(get_kv(item, 'n'), '#file55')
            
            # False Examples
            if test_line == '[^TL3..5]':
                self.assertEqual(get_kv(item, 'code'), 'TL3..5')
                self.assertEqual(get_kv(item, 'n'), '')

    def test_can_parse_citation_lines(self):
        test_lines_dict = {
            'G0.0': '- 240701-W27T 21:52 - [^T1]: Update Task-Notelog solution to work with argparse interface #548991db',
            'G0.1': '   - 240708-W28M 06:57 - [^CMT1]: 5ff942c (HEAD -> main) feat[TaskGraph]: Added ArgParse and Clustered multiline grep',
            'G0.2': '- 240701-W27S 18:31 - [^FL2.1]: WSL, $HOME/src/ttm/ttm-tools/bin/tmlib.notes-citations-processor.py',
            'G0.3': '   - 240701-W27M 09:02 - [^T5]: (-) /T::milestone_of/ TaskGraph: Impl parsing for Citation Notelog #e142cb79',
            'G0.4': '                    - 240701-W27M 04:47 - [^T1]: /T::spawned_by/    TaskGraph: Extend tmlib.note-parser to account for multiline log lines\n' +
                    '                                                 (!) /T::solved_by/',
            'G0.5': '                - 240701-W27R 19:58 - [^T1]: /T::is_self/ TaskGraph::MSTN: Able to render graph representation of tasks/citations\n' +
                    '                                             (-) /T::blocks(milestone)/',
            'G0.6': '- 240715-W29T 16:21 - [^FL#ntp_src]: WSL, $HOME/src/ttm/ttm-tools/bin/tmlib.note-parser.py',

            # False non-parsing examples
            'NP1': '- 240701-W27S 18:45 - With help of [^GT1]:',
            'NP2': '- 240701-W27M 06:00 - [^NT1]::Iteration3 shows that we successfully trigger the condition on each two new lines for the last long line.',
        }

        for test_no in test_lines_dict:
            test_line = test_lines_dict[test_no]
            item = Item.parse(ItemType.CITATION_LINE, test_line)

            # Just immediately display it for quick debugging
            item_str = str(item) 
            log_debug(f'citation lines: test input: {test_no}: {test_line}')
            log_debug(item_str)

            # False non-parsing examples

            if test_no.startswith('NP'):
                self.assertTrue(item == None)
                continue

            # Parsing Examples
            self.assertTrue(item != None)
            self.assertEqual(item.value, test_line)

            # 'G0.0': '- 240701-W27T 21:52 - [^T1]: Update Task-Notelog solution to work with argparse interface #548991db',
            if test_no == 'G0.0':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240701-W27T 21:52')
                self.assertEqual(get_kv(time_date, 'date_code'), '240701')
                self.assertEqual(get_kv(time_date, 'week_num'), '27')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'T')
                self.assertEqual(get_kv(time_date, 'HH'), '21')
                self.assertEqual(get_kv(time_date, 'MM'), '52')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'T')
                self.assertEqual(get_kv(cite_code, 'n'), '1')

                self.assertEqual(get_kv(item, 'uuid'), '548991db')

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('Update Task-Notelog'))
                self.assertTrue(desc.endswith('argparse interface'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertEqual(relations, None)

            # 'G0.1': '   - 240708-W28M 06:57 - [^CMT1]: 5ff942c (HEAD -> main) feat[TaskGraph]: Added ArgParse and Clustered multiline grep',
            if test_no == 'G0.1':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '   ')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240708-W28M 06:57')
                self.assertEqual(get_kv(time_date, 'date_code'), '240708')
                self.assertEqual(get_kv(time_date, 'week_num'), '28')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'M')
                self.assertEqual(get_kv(time_date, 'HH'), '06')
                self.assertEqual(get_kv(time_date, 'MM'), '57')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'CMT')
                self.assertEqual(get_kv(cite_code, 'n'), '1')

                self.assertEqual(get_kv(item, 'uuid'), None)

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('5ff942c (HEAD -> main)'))
                self.assertTrue(desc.endswith('multiline grep'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertEqual(relations, None)

            # 'G0.2': '- 240701-W27S 18:31 - [^FL2.1]: WSL, $HOME/src/ttm/ttm-tools/bin/tmlib.notes-citations-processor.py'
            if test_no == 'G0.2':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240701-W27S 18:31')
                self.assertEqual(get_kv(time_date, 'date_code'), '240701')
                self.assertEqual(get_kv(time_date, 'week_num'), '27')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'S')
                self.assertEqual(get_kv(time_date, 'HH'), '18')
                self.assertEqual(get_kv(time_date, 'MM'), '31')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'FL')
                self.assertEqual(get_kv(cite_code, 'n'), '2.1')

                self.assertEqual(get_kv(item, 'uuid'), None)

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('WSL, '))
                self.assertTrue(desc.endswith('processor.py'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertEqual(relations, None)

            # 'G0.3': '   - 240701-W27M 09:02 - [^T5]: (-) /T::milestone_of/ TaskGraph: Impl parsing for Citation Notelog #e142cb79',
            if test_no == 'G0.3':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '   ')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240701-W27M 09:02')
                self.assertEqual(get_kv(time_date, 'date_code'), '240701')
                self.assertEqual(get_kv(time_date, 'week_num'), '27')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'M')
                self.assertEqual(get_kv(time_date, 'HH'), '09')
                self.assertEqual(get_kv(time_date, 'MM'), '02')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'T')
                self.assertEqual(get_kv(cite_code, 'n'), '5')

                self.assertEqual(get_kv(item, 'uuid'), 'e142cb79')

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('TaskGraph: Impl'))
                self.assertTrue(desc.endswith('Notelog'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertEqual(get_kv(relations, 'node'), 'T')
                self.assertEqual(get_kv(relations, 'relation'), 'milestone_of')
                self.assertEqual(get_kv(relations, 'is_from'), 'True')
                self.assertEqual(get_kv(relations, 'status'), '-')
        

            # 'G0.4': '                    - 240701-W27M 04:47 - [^T1]: /T::spawned_by/    TaskGraph: Extend tmlib.note-parser to account for multiline log lines\n' +
            #         '                                                 (!) /T::solved_by/',
            if test_no == 'G0.4':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '                    ')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240701-W27M 04:47')
                self.assertEqual(get_kv(time_date, 'date_code'), '240701')
                self.assertEqual(get_kv(time_date, 'week_num'), '27')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'M')
                self.assertEqual(get_kv(time_date, 'HH'), '04')
                self.assertEqual(get_kv(time_date, 'MM'), '47')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'T')
                self.assertEqual(get_kv(cite_code, 'n'), '1')

                self.assertEqual(get_kv(item, 'uuid'), None)

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('TaskGraph: Extend'))
                self.assertTrue(desc.endswith('log lines'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertTrue(type(relations) is list)
                self.assertTrue(len(relations) == 2)
                self.assertEqual(get_kv(relations[0], 'node'), 'T')
                self.assertEqual(get_kv(relations[0], 'relation'), 'spawned_by')
                self.assertEqual(get_kv(relations[0], 'is_from'), 'True')
                self.assertEqual(get_kv(relations[0], 'status'), None)
                self.assertEqual(get_kv(relations[1], 'node'), 'T')
                self.assertEqual(get_kv(relations[1], 'relation'), 'solved_by')
                self.assertEqual(get_kv(relations[1], 'is_from'), 'True')
                self.assertEqual(get_kv(relations[1], 'status'), '!')

            # 'G0.5': '                - 240701-W27R 19:58 - [^T1]: /T::is_self/ TaskGraph::MSTN: Able to render graph representation of tasks/citations\n' +
            #         '                                             (-) /T::blocks(milestone)/',
            if test_no == 'G0.5':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '                ')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240701-W27R 19:58')
                self.assertEqual(get_kv(time_date, 'date_code'), '240701')
                self.assertEqual(get_kv(time_date, 'week_num'), '27')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'R')
                self.assertEqual(get_kv(time_date, 'HH'), '19')
                self.assertEqual(get_kv(time_date, 'MM'), '58')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'T')
                self.assertEqual(get_kv(cite_code, 'n'), '1')

                self.assertEqual(get_kv(item, 'uuid'), None)

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('TaskGraph::MSTN: Able to render'))
                self.assertTrue(desc.endswith('tasks/citations'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertTrue(type(relations) is list)
                self.assertTrue(len(relations) == 2)
                self.assertEqual(get_kv(relations[0], 'node'), 'T')
                self.assertEqual(get_kv(relations[0], 'relation'), 'is_self')
                self.assertEqual(get_kv(relations[0], 'is_from'), 'True')
                self.assertEqual(get_kv(relations[0], 'status'), None)
                self.assertEqual(get_kv(relations[1], 'node'), 'T')
                self.assertEqual(get_kv(relations[1], 'relation'), 'blocks(milestone)')
                self.assertEqual(get_kv(relations[1], 'is_from'), 'True')
                self.assertEqual(get_kv(relations[1], 'status'), '-')

            # 'G0.6': '- 240715-W29T 16:21 - [^FL#ntp_src]: WSL, $HOME/src/ttm/ttm-tools/bin/tmlib.note-parser.py',
            if test_no == 'G0.6':
                tab_level = item.get_part(ItemType.TAB_LEVEL).value
                self.assertEqual(tab_level, '')

                time_date = item.get_part(ItemType.TIME_DATE)
                self.assertEqual(time_date.value, '240715-W29T 16:21')
                self.assertEqual(get_kv(time_date, 'date_code'), '240715')
                self.assertEqual(get_kv(time_date, 'week_num'), '29')
                self.assertEqual(get_kv(time_date, 'MTWRFSU'), 'T')
                self.assertEqual(get_kv(time_date, 'HH'), '16')
                self.assertEqual(get_kv(time_date, 'MM'), '21')

                cite_code = item.get_part(ItemType.CITE_CODE)
                self.assertEqual(get_kv(cite_code, 'code'), 'FL')
                self.assertEqual(get_kv(cite_code, 'n'), '#ntp_src')

                self.assertEqual(get_kv(item, 'uuid'), None)

                desc = get_kv(item, 'desc')
                self.assertTrue(desc.startswith('WSL, '))
                self.assertTrue(desc.endswith('parser.py'))

                relations = item.get_part(ItemType.CITE_RELATION)
                self.assertEqual(relations, None)

        pass

if __name__ == '__main__':
    _main()