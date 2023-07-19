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
        priority = tokens[7].strip()

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


class CalcureEventsFile:
    def __init__(self, filename: str):
        with open(filename, 'r') as f:
            csv_lines = f.readlines()

        # parse csv file
        events: List[CalcureCsvEvent] = []
        for line in csv_lines:
            events.append(CalcureCsvEvent.parse(line))
        
        self.events = events
        self.filename = filename
    
    def save(self):
        lines = []
        for i, event in enumerate(self.events):
            lines.append(event.display(i))

        with open(self.filename, 'w') as f:
            f.writelines(lines)
    
    def sort(self):
        events_sorted = sorted(self.events, key=lambda e: (int(e.year), int(e.month), int(e.day), int(e.start)))
        self.events = events_sorted
    