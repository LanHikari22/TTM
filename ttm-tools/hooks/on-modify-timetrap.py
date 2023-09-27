import sys
import os
import json
import subprocess
from typing import List, Tuple

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
    

def system_run(cmd: str) -> str:
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    output = ps.communicate()[0]
    return output


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


def pipe_print(s, tty=25):
    system_run('echo \'{}\' > /dev/pts/{}'.format(s, tty))


def main():
    in_json = json.loads(sys.argv[1])
    prev_json = None

    # timetrap_current_name = timetrap_get_running_name()

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

    timetrap_name = timetrap_parse_name(in_json)
    if timetrap_name == '':
        # nothing to do based on this action
        return 0

    # pipe_print('debug: "{}"'.format(timetrap_name))

    started, stopped = check_started_trigger(in_json, prev_json)
    # pre_print('debug: (Started: {}, Stopped: {})'.format(started, stopped))


    if started and not stopped:
        # system_run("powershell.exe New-BurntToastNotification -Text \"timetrap_start\"")
        system_run('timetrap out && timetrap in "{}"'.format(timetrap_name))
    if not started and stopped:
        # system_run("powershell.exe New-BurntToastNotification -Text \"timetrap_stop\"")
        system_run('timetrap out')
    
    return 0

if __name__ == '__main__':
    exit(main())
    
