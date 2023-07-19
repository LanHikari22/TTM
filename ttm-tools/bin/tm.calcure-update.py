import argparse
import sys
import json
from typing import List

class CalcureCsvEvent:
    def __init__(self, year, month, day, start, end, tag, desc, repeat_amt, repeat_mode, priority,
                 gcode=None, uuid=None, project=None, item_desc=None):
        self.year = year
        self.month = month
        self.day = day
        self.start = start
        self.end = end
        self.tag = tag
        self.desc = desc
        self.repeat_amt = repeat_amt
        self.repeat_mode = repeat_mode
        self.priority = priority
        self.gcode = gcode
        self.uuid=uuid
        self.project = project
        self.item_desc = item_desc

    @staticmethod
    def parse(csv_line: str) -> 'CalcureCsvEvent':
        tokens = csv_line.split(',')
        if len(tokens) != 8:
            raise Exception(f'Calcure event csv line must have 8 comma-seperated tokens. Line: {csv_line}')

        _id = tokens[0]
        year = tokens[1]
        month = tokens[2]
        day = tokens[3]
        desc = tokens[4]
        repeat_amt = tokens[5]
        repeat_mode = tokens[6]
        priority = tokens[7]

        # process out start-end from description. Required.
        if len(desc) < len('"0000:0000 ') or desc[5] != ':':
            raise Exception(f'Description must start with time stamp like 0000:0000. Desc: {desc}')
        desc_split = desc.split(':')
        start = desc_split[0][1:]
        end = desc_split[1][:4]
        desc_remaining = ':'.join(desc_split[1:])[5:-1]

        # Every item should have a unique tag
        desc_remaining_tokens = desc_remaining.split(' ')
        if len(desc_remaining_tokens) < 2 or len(desc_remaining_tokens[0]) != 4:
            raise Exception(f'Description must start with a 4 character tag like EVNT. Desc: {desc_remaining}')
        tag = desc_remaining_tokens[0]
        desc_remaining = ' '.join(desc_remaining_tokens[1:])

        # Try to parse extra information from the description if possible: gcode, UUID, project, item_desc (remaining)
        desc_remaining_tokens = desc_remaining.split(' ')
        gcode = None
        uuid = None
        project = None
        item_desc = None
        if len(desc_remaining_tokens) >= 4:
            gcode = desc_remaining_tokens[0]
            uuid = desc_remaining_tokens[1]

            # Since this is a variable length field, assumme some default padding
            project = desc_remaining_tokens[2]
            project = project + ' ' * (max(0, len('some_long_project_name') - len(project)))
            item_desc = ' '.join(desc_remaining_tokens[3:]).strip()


        return CalcureCsvEvent(year, month, day, start, end, tag, desc_remaining, repeat_amt, repeat_mode, priority,
                               gcode, uuid, project, item_desc)


    def display(self, event_id: int) -> str:
        #if self.gcode != None:
        #    return f'{event_id},{self.year},{self.month},{self.day},"{self.start}:{self.end} {self.gcode} {self.uuid} {self.project} {self.item_desc}",{self.repeat_amt},{self.repeat_mode},{self.priority}'
        #else:
        #    return f'{event_id},{self.year},{self.month},{self.day},"{self.start}:{self.end} {self.desc}",{self.repeat_amt},{self.repeat_mode},{self.priority}'
        return f'{event_id},{self.year},{self.month},{self.day},"{self.start}:{self.end} {self.tag} {self.desc}",{self.repeat_amt},{self.repeat_mode},{self.priority}'


def reorder_events():
    with open(args.events_csv, 'r') as f:
        csv_lines = f.readlines()

    # parse csv file
    try:
        events: List[CalcureCsvEvent] = []
        for line in csv_lines:
            events.append(CalcureCsvEvent.parse(line))
    except Exception as e:
        print(f'Exception: {e}')
        return 2

    # sort items by year, month, day, and start time.
    events_sorted = sorted(events, key=lambda e: (int(e.year), int(e.month), int(e.day), int(e.start)))

    # transform back to lines
    sorted_lines = []
    for i, event in enumerate(events_sorted):
        sorted_lines.append(event.display(i))

    # write new sorted csv
    with open(args.events_csv, 'w') as f:
        f.writelines(sorted_lines)

    print('Sorted calcure events')
    return 0


def parse_args():
    sys.argv[0] = 'calcure-update'

    p = argparse.ArgumentParser(description='handles Calcure update operations',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='increase output verbosity (default: %(default)s)')

    p.add_argument('events_csv',
                   help='Path to events file to process')

    p.add_argument('action', choices=['reorder-events'],
                   help='Action to perform')

    #  p.add_argument('required_positional_arg',
                   #  help='desc')
    #  p.add_argument('required_int', type=int,
                   #  help='req number')
    #  p.add_argument('--on', action='store_true',
                   #  help='include to enable')

    args = p.parse_args()

    return args

if __name__ == '__main__':
    args = parse_args()

    if args.action == 'reorder-events':
        exit(reorder_events())
