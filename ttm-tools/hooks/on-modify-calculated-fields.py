import sys
import json
import subprocess
from typing import List, Tuple

def system_run(cmd: str) -> str:
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    output = ps.communicate()[0]
    return output

def pipe_print(s, tty=25):
    system_run(f'echo \'{s}\' > /dev/pts/{tty}')

def log_debug(s, log_filename=sys.argv[0] + '.log'):
    from datetime import datetime as dtdt

    with open(log_filename, 'a') as f:
        f.write(f'{str(dtdt.now())} debug: {s}\n')

# -------------------------------------------------------------------------------------------------
def to_short_uuid(long_uuid: str):
    return long_uuid.split('-')[0]

# -------------------------------------------------------------------------------------------------
def timetrap_parse_name(in_json) -> bool:
    """
    processes the expected timetrap note from this task JSON.
    if no tags are specified, or 'tNoTrack' is specified in the tags, then return '' else
    return something like 'UUID p(proj) tTag1 tTag2 ... Description'
    """
    # short uuid must be included for accurate mapping of entries
    uuid: str = in_json['uuid']
    if uuid != None and uuid != '':
        uuid = uuid[:uuid.index('-')] + ' '
    else:
        uuid = ''

    # gcode will match entries against broader goals that can spam across projects
    gcode = ''
    if 'gcode' in in_json:
        gcode = in_json['gcode']
        if gcode != None and gcode != '':
            gcode += ' '


    # projects are denoted p(project)
    if 'project' not in in_json:
        return ''
    proj: str = in_json['project']
    if proj != None and proj != '':
        proj = 'p(' + proj + ') '
    else:
        proj = ' '
    
    # process timetrap tags. they start with t followed by a capital letter
    tags = []
    if 'tags' not in in_json:
        return ''
    for tag in in_json['tags']:
        if tag.startswith('t') and len(tag) > 1 and tag[1].isupper():
            tags.append(tag)
    

    # if no tags are found, this task shouldn't be tracked.
    # if tNoTrack is found, do not track this entry
    if tags == [] or 'tNoTrack' in tags:
        return ''

    res = proj + uuid + gcode
    for tag in tags:
        res += tag
    res += '- ' + in_json['description']

    return res.strip()

def timetrap_get_running_name() -> str:
    """
    gets the currently running timetrap entry or ''
    """
    res = system_run('timetrap -fjson today')
    timetrap_json = json.loads(res)

    if len(timetrap_json) == 0:
        return ''
    
def task_parse_last_log_entry(uuid) -> str:
    stdout = system_run('task ' + uuid + ' | tail -n2' + ' | head -n1')
    return str(stdout)

def is_task_started(log_entry: str) -> bool:
    if 'Start set to' in log_entry:
        return True
    return False

def is_task_stopped(log_entry: str) -> bool:
    if 'Start deleted' in log_entry:
        return True
    return False

def task_find_last_start_stop_log_entry(uuid) -> str:
    stdout = str(system_run('task ' + uuid)).replace('\\n', '\n')

    # traverse the lines from the end, find the first start or stopped entry
    lines = stdout.split('\n')
    lines.reverse()
    for entry in lines:
        if is_task_started(entry) or is_task_stopped(entry):
            return entry

    return ''

def check_started_trigger(cur_json, prev_json) -> Tuple[bool, bool]:
    """
    we check whether this action started or stopped the task by checking for the 'start'
    property of the JSON which is toggled. For this, we need the previous one to determine the edge
    state. If no previous json is found, and this is started, it is started. Otherwise, it's
    based on trigger.

    returns (started, stopped) to determine which action occured
    """

    was_started = False
    if prev_json is not None and prev_json['uuid'] == cur_json['uuid']:
        was_started = 'start' in prev_json and prev_json['start'] != ''
    is_started = 'start' in cur_json and cur_json['start'] != ''
    # pipe_print('check({}, {})'.format(was_started, is_started))

    if (was_started and is_started) or (not was_started and not is_started):
        return (False, False)

    if not was_started and is_started:
        return (True, False)
    
    if was_started and not is_started:
        return (False, True)
    
    return (False, False)   # unreachable

def timetrap_parse_time(s):
    from datetime import datetime as dtdt

    return dtdt.strptime(s, '%Y-%m-%d %H:%M:%S %z')

def timetrap_get_entries_for_uuid(uuid: str, subtask_pattern: str) -> List[dict]:
    if subtask_pattern == '':
        result = system_run(f'timetrap -fjson d -g{uuid}')
    else:
        result = system_run(f'timetrap -fjson d -g{subtask_pattern}')

    if result == b'':
        return []

    try:
        result = json.loads(result)
    except Exception as e:
        log_debug(f'timetrap result {result}')
        log_debug(f'Error for timetrap, {e}')
        return []

    if type(result) is dict:
        return [result]
    elif type(result) is list:
        return result
    else:
        return []

def timetrap_get_total_time(timetrap_json: List[dict], uuid: str) -> int:
    """
    Args:
        timetrap_json (_type_): Json output of timetrap filtered for uuid.
        uuid (str): The uuid to get total time for

    Returns:
        int: Total Time for task in seconds, excluding any subtasks
    """
    from datetime import timedelta

    result = timedelta()
    for entry in timetrap_json:
        if f' {uuid} ' in entry['note']:
            end = timetrap_parse_time(entry['end'])
            start = timetrap_parse_time(entry['start'])
            result += end - start
    
    return result.total_seconds()


def timetrap_get_cumulative_time(timetrap_json, uuid: str, subtask_pattern: str) -> int:
    from datetime import timedelta

    result = timedelta()
    for entry in timetrap_json:
        if subtask_pattern != '':
            self_or_subtask = subtask_pattern in entry['note']
        else:
            self_or_subtask = f' {uuid} ' in entry['note'] or f' {uuid}.' in entry['note']

        if self_or_subtask:
            end = timetrap_parse_time(entry['end'])
            start = timetrap_parse_time(entry['start'])
            result += end - start

    return result.total_seconds()

def update_blk_fields(in_json: dict, out_json: dict, uuid: str, subtask_pattern: str) -> bool:
    # update blkput based on times from timetrap

    modified = False
    calculate = 'tags' in in_json and 'noblk' not in in_json['tags']

    if not calculate:
        if 'blkput' in in_json:
            out_json['blkput'] = ''
            modified = True

        if 'blkputcum' in in_json:
            out_json['blkputcum'] = ''
            modified = True
        
        return modified
        
    timetrap_entries = timetrap_get_entries_for_uuid(uuid, subtask_pattern)
    total_time = timetrap_get_total_time(timetrap_entries, uuid) // 60 // 20
    cum_time = timetrap_get_cumulative_time(timetrap_entries, uuid, subtask_pattern) // 60 // 20

    #  log_debug(f'uuid={uuid}, subtask_pattern={subtask_pattern}')
    #  log_debug(f'entries: {timetrap_entries}')
    #  log_debug(f'tottime: {total_time}')
    #  log_debug(f'cumtime: {cum_time}')

    if total_time != 0 and ('blkput' not in in_json or total_time != out_json['blkput']):
        out_json['blkput'] = total_time
        modified = True

    if cum_time != 0 and ('blkputcum' not in in_json or cum_time != out_json['blkputcum']):
        out_json['blkputcum'] = cum_time
        modified = True

    if 'blkputman' in in_json:
        out_json['blkput'] += in_json['blkputman']
        out_json['blkputcum'] += in_json['blkputman']
        modified = True

    if 'blkput' in out_json and out_json['blkput'] == 0:
        out_json['blkput'] = ''
        modified = True

    if 'blkputcum' in out_json and out_json['blkputcum'] == 0:
        out_json['blkputcum'] = ''
        modified = True

    # update blkrem: blkest - blkput
    if 'blkest' in in_json and 'blkputcum' in out_json:
        blkputcum = 0.0 if out_json['blkputcum'] == '' else out_json['blkputcum']
        out_json['blkrem'] = in_json['blkest'] - blkputcum
        modified = True
    
    return modified

# -------------------------------------------------------------------------------------------------
def load_cached_prev_json():
    # load previous json state if stored, and store latest input instead
    tmp_file_path: str = sys.argv[0] + '.json.tmp'
    with open(tmp_file_path, 'r+') as tmp_file:
        res = str(tmp_file.read()).replace('\0', '')
        # pipe_print('res: {}'.format(res))
        if res != '':
            prev_json = json.loads(str(res))
        # clear and store latest input
        tmp_file.truncate(0)
        tmp_file.write(sys.argv[1])
    # pipe_print('debug: ' + json.dumps(in_json, indent=4))

    return prev_json

# -------------------------------------------------------------------------------------------------
def main() -> int:
    in_json = json.loads(sys.argv[1])
    out_json = in_json
    modified = False
    # prev_json = load_cached_prev_json()

    if 'uuid' not in in_json:
        print(sys.argv[1])
        return 0

    uuid = to_short_uuid(in_json['uuid'])

    subtask_pattern = in_json['description'].split(' ')[0]
    #  log_debug(f'subtask_pattern? {subtask_pattern}')
    if len(subtask_pattern) < len(uuid) + 1 or subtask_pattern[len(uuid)] != '.':
        subtask_pattern = ''

    if update_blk_fields(in_json, out_json, uuid, subtask_pattern):
        modified = True

    # log_debug(f'Hi! in_json:\n{in_json}\n\n')
    # log_debug(f'Bye! out_json:\n{out_json}\n\n')

    if modified:
        print(json.dumps(out_json))
    else:
        print(sys.argv[1])

    return 0

if __name__ == '__main__':
    exit(main())
    
