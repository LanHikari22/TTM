"""
Generate a JSON report of time allocated, achievd.
"""

class EntryTime:
    def __init__(self, hours: int, minutes: int, interval: bool):
        self.hours = hours
        self.minutes = minutes
        self.interval = interval


class ReportEntry:
    def __init__(self, start: EntryTime, end: EntryTime, gcode: str, uuid: str, proj: str, desc: str):
        self.start = start
        self.end = end
        self.gcode = gcode
        self.uuid = uuid
        self.proj = proj
        self.desc = desc

    @staticmethod
    def from_csv_line(line: str) -> 'ReportEntry':
        raise Exception('Not implemented')


class Report:
    pass



if __name__ == '__main__':
    pass
