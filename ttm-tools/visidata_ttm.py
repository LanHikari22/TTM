import os
import pandas as pd
import numpy as np
import pipe
import json
from pipe import Pipe
from typing import List, Tuple

import visidata
from visidata import (  # ColumnAttr,; options,
    Column,
    ItemColumn,
    TableSheet,
    TypedExceptionWrapper,
    VisiData,
    date,
    stacktrace,
    vd,
    ALT,
    Sheet,
    BaseSheet
)

module_input = globals()['module_input']

SelectCommand = module_input['SelectCommand']
Common = module_input['Common']


def is_valid_blocktracker_df(df: pd.DataFrame) -> bool:
    index = pd.Index(['pri', 'gcode', 'M', 'T', 'W', 'R', 'F', 'S', 'U', 'WSUM'], 
                        dtype='object')
    
    matching_columns = len(df.columns) == len(index) and (df.columns == index).all()

    if not matching_columns:
        return False

    return True


def is_valid_schedule_df(df: pd.DataFrame) -> bool:
    index = pd.Index(['HA', 'A000', 'A020', 'A040', 'A100', 'A120', 'A140', '    ', 
                        'HP', 'P000', 'P020', 'P040', 'P100', 'P120', 'P140'], 
                        dtype='object')
    matching_columns = (df.columns == index).all()

    if not matching_columns:
        return False

    return True


class BlockTrackerAutoCompute(SelectCommand):
    def __init__(self, key: str, schedule_json_path: str, 
                    exec=['autocompute', '!view_inverted']):
        self._key = key
        self.schedule_json_path = schedule_json_path
        self.exec = exec

    def key(self) -> str: return self._key

    def name(self) -> str: 
        if 'autocompute' in self.exec:      return 'BlockTracker.AutoCompute'
        if 'view_inverted' in self.exec:    return 'BlockTracker.ViewInverted'
        raise SelectCommand.Error('No command to execute')

    def help(self) -> str: 
        if 'autocompute' in self.exec:      return 'Computes field values on trigger'
        if 'view_inverted' in self.exec:    return 'Creates a sheet with inverted sum column to see remaining'
        
        raise SelectCommand.Error('No command to execute')

    def run(self, sheet):
        if 'autocompute' in self.exec:      return self.run_autocompute(sheet)
        if 'view_inverted' in self.exec:    return self.run_view_inverted(sheet)
        raise SelectCommand.Error('No command executed')

    def parse_goal_stats(self, df_sch: pd.DataFrame):
        """
        Processes a dictionary by goal key and weekcount stats:
            {goal: {'M': T, 'T': T, 'W': T, 'R': T, 'F': T, 'S': T, 'U': T}}
                where
                    T is Tuple[int, int, statusA, statusP] for actual and planned 
                    and aggregated statuses.
        """
        result = {}

        def create_empty_goal_dict():
            tup = (0, 0, '', '')
            return {'M': tup, 'T': tup, 'W': tup, 'R': tup, 'F': tup, 'S': tup, 'U': tup}

        def proceess_stats(v_arr, is_v_A: bool):
            for code in v_arr:
                if len(code) < 4:
                    continue

                gcode = code[:4]
                if not gcode[-1].isdigit():
                    continue

                flags = ''
                if len(code) > 4:
                    flags = code[4:]
                
                if gcode not in result:
                    result[gcode] = create_empty_goal_dict()
                
                tup = result[gcode][d]

                if is_v_A:
                    # we've encontered this gcode now. so increment actual count and aggregate flags
                    result[gcode][d] = (tup[0]+1, tup[1], tup[2] + flags, tup[3])
                else:
                    result[gcode][d] = (tup[0], tup[1]+1, tup[2], tup[3] + flags)

        df_sch_t = df_sch.T

        for r in df_sch_t:
            # extract values at specific time period r
            v_HA = df_sch_t[r]['HA'].strip()
            v_HP = df_sch_t[r]['HP'].strip()
            v_A = [df_sch_t[r]['A000'], df_sch_t[r]['A020'], df_sch_t[r]['A040'], 
                    df_sch_t[r]['A100'], df_sch_t[r]['A120'], df_sch_t[r]['A140'], ]
            v_P = [df_sch_t[r]['P000'], df_sch_t[r]['P020'], df_sch_t[r]['P040'], 
                    df_sch_t[r]['P100'], df_sch_t[r]['P120'], df_sch_t[r]['P140'], ]

            # ensure HA and HP are always identical
            if v_HA != v_HP:
                raise SelectCommand.Error(
                    f'Expected HA and HP to be identical: "{v_HA}" != "{v_HP}"')

            # skip timeless entries
            if v_HA == '':
                continue

            # parse v_HA time and day
            _t = int(v_HA[:-1])
            d = v_HA[-1]

            if d not in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                raise SelectCommand.Error(f'Expected valid day code for {d}')
            
            # go through the codes available and populate our stats
            proceess_stats(v_A, is_v_A=True)
            proceess_stats(v_P, is_v_A=False)
        
        return result
    
    def process_total_row(self, result: pd.DataFrame) -> int:
        modified = 0

        # process column total
        if 'DSUM' in result['gcode'].values:
            df_bt_not_tot = result[result['gcode'] != 'DSUM']
            df_bt_tot = result[result['gcode'] == 'DSUM'] 

            for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U', 'WSUM', 'WREM']:
                if day not in df_bt_not_tot:
                    continue

                lst = df_bt_tot[day][0]

                # Find how much was done, but do not count anything beyond expectations
                total_expected_done = df_bt_not_tot[day] \
                    .apply(lambda lst: min(lst[0], lst[1]) if lst[0] != -1 and lst[1] != -1 else 0) \
                    .sum()

                total_planned = df_bt_not_tot[day] \
                    .apply(lambda lst: lst[1] if lst[1] != -1 else 0) \
                    .sum()

                
                total_planned_2 = lst[2] if day != 'WSUM' else df_bt_not_tot[day] \
                    .apply(lambda lst: lst[2] if lst[2] != -1 else 0) \
                    .sum()
                
                pct = total_expected_done / total_planned if total_planned != 0 else 0.0
                pct = round(pct, 2)
                
                try:
                    new_lst = [total_expected_done, total_planned, total_planned_2, pct, lst[4]]
                except IndexError:
                    raise IndexError(f'Somw columns in DSUM do not have enough rows (expecting 4): {lst}')

                # thought I gotta do this trickery, multi-assignment failing on list-like objects.
                # new_list_arr = np.tile(new_lst, (1,1)).T

                result.loc[df_bt_tot.index[0], day] = new_lst
                modified += 1
        
        return modified

    def update_blocktracker_with_schdule_stats(self, df_bt: pd.DataFrame, goal_stats
                                                ) -> Tuple[int, pd.DataFrame]:

        df_bt_t = df_bt.T
        df_result_t = df_bt_t.copy()
        modified = 0

        def process_day(d, stats):
            lst = df_result_t[r][d].copy()
            act, planned, flags_a, flags_p = stats[d]
            flags = flags_a + flags_p

            changed = lst[0] != act or lst[2] != flags

            if changed:
                df_result_t[r][d] = [act, lst[1], lst[2], flags]
                return 1
            return 0

        for r in df_bt_t:
            v_gcode = df_bt_t[r]['gcode']

            if v_gcode == 'DSUM':
                continue

            if v_gcode in goal_stats:
                stats = goal_stats[v_gcode]

                for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                    modified += process_day(day, stats)
            
            # process total column as week sum
            if 'WSUM' in df_bt_t[r]:
                lst = df_result_t[r]['WSUM'] 
                sum_stats = [0, 0, lst[2], 0.0, lst[4]]
                for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                    day_stats = df_result_t[r][day]
                    total_done = int(day_stats[0])
                    planned = int(day_stats[1])

                    sum_stats = [sum_stats[0] + total_done, sum_stats[1] + planned,
                                 sum_stats[2], 0.0, sum_stats[4]]

                pct = sum_stats[0] / sum_stats[1] if sum_stats[1] != 0 else 0.0
                pct = round(pct, 2)
                sum_stats = [sum_stats[0], sum_stats[1], sum_stats[2], pct, sum_stats[4]]

                df_result_t[r]['WSUM'] = sum_stats
                modified += 1

                
        result = df_result_t.T

        modified += self.process_total_row(result)
        
        return (modified, result)

    def invert_blocktracker_sum_column(self, df_bt, goal_stats):
        df_result = df_bt.copy()

        df_result['WREM'] = df_result['WSUM']
        df_result_t = df_result.T

        df_bt_t = df_bt.T
        modified = 0

        for r in df_bt_t:
            v_gcode = df_bt_t[r]['gcode']

            if v_gcode == 'DSUM':
                continue

            # process inverted total column as week remaining
            if 'WREM' in df_result_t[r]:
                lst = df_result_t[r]['WREM'] 
                sum_stats = [0, 0, lst[2], 0.0, lst[4]]

                for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                    day_stats = df_result_t[r][day]
                    total_done = int(day_stats[0])
                    planned = int(day_stats[1])

                    sum_stats = [sum_stats[0] + total_done, sum_stats[1] + planned, 
                                 sum_stats[2], 0.0, sum_stats[4]]

                pct = sum_stats[0] / sum_stats[1] if sum_stats[1] != 0 else 0.0
                pct = max(0.0, round(1.00 - pct, 2))
                remaining = max(0, sum_stats[1] - sum_stats[0])

                sum_stats = [remaining, sum_stats[1], sum_stats[2], pct, sum_stats[4]]
                df_result_t[r]['WREM'] = sum_stats

                modified += 1
                
        result = df_result_t.T

        modified += self.process_total_row(result)
        
        return (modified, result)

    def load_dataframes(self, sheet, check_sheet=False):
        df_bt = pd.DataFrame.from_records(sheet.rows)
        if not is_valid_blocktracker_df(df_bt):
            if check_sheet: return (None, None)
            raise SelectCommand.Error('Invalid BlockTracker sheet')
        
        df_schs = pd.read_json(self.schedule_json_path)

        weekdatecode = sheet.xls_name
        if weekdatecode not in df_schs:
            raise SelectCommand.Error(f'Could not find schedule weekdatecode {weekdatecode}')
        
        df_sch = pd.DataFrame(df_schs[weekdatecode][0])
        if not is_valid_schedule_df(df_sch):
            raise SelectCommand.Error('Invalid Scheduler json data')
        
        goal_stats = self.parse_goal_stats(df_sch)

        return (df_bt, goal_stats)
    
    def run_autocompute(self, sheet):
        for sheet in vd.sheets:
            df_bt, goal_stats = self.load_dataframes(sheet, check_sheet=True)
            if df_bt is None and goal_stats is None:
                continue

            modified, df_bt = self.update_blocktracker_with_schdule_stats(df_bt, goal_stats)
            if modified == 0:
                raise SelectCommand.Error('No entry to modify')

            # update sheet
            rows = df_bt.to_dict('records')
            modified = Common.sheet_update_cells(sheet, rows)
            vd.status(f'Updated {modified} entries')

    def run_view_inverted(self, sheet):
        df_bt, goal_stats = self.load_dataframes(sheet)

        modified, df_bt = self.invert_blocktracker_sum_column(df_bt, goal_stats)
        if modified == 0:
            raise SelectCommand.Error('No modification was made to view')

        vd.view(df_bt.to_dict('records'))


class BlockTrackerFileSystem(SelectCommand):
    def __init__(self, key: str, 
                 exec=['copy', 'remove', 'move', 'clear', 'cust']):
        self._key = key
        self.exec = exec

    def key(self) -> str: return self._key

    def name(self) -> str: 
        if 'copy' in self.exec: return 'Entry Copy'
        if 'remove' in self.exec: return 'Entry Remove'
        if 'move' in self.exec: return 'Entry move'
        if 'clear' in self.exec: return 'BlockTracker.Clear'
        if 'cust' in self.exec: return 'Entry cust'
        raise SelectCommand.Error('No command to execute')

    def help(self) -> str: 
        if 'copy' in self.exec: return 'Copies a new entry from an old one'
        if 'remove' in self.exec: return 'Removes a entry'
        if 'move' in self.exec: return 'Renames an entry'
        if 'clear' in self.exec: return 'Clears a BlockTracker entry so that all values are zero.'
        if 'cust' in self.exec: return 'Custom command for testing purposes or one-time operations'
        raise SelectCommand.Error('No command to execute')

    def run(self, sheet):
        if 'copy' in self.exec: return self.run_copy(sheet)
        if 'remove' in self.exec: return self.run_remove(sheet)
        if 'move' in self.exec: return self.run_move(sheet)
        if 'clear' in self.exec: return self.run_clear(sheet)
        if 'cust' in self.exec: return self.run_cust(sheet)
        raise SelectCommand.Error('No command to execute')

    def load_path_sheet_dataframe(self) -> pd.DataFrame:
        try:
            path_sheet = vd.sheets | pipe.where(Common.is_path_sheet) | Pipe(next)
        except StopIteration:
            raise SelectCommand.Error('Could not find path sheet')
        
        return path_sheet, pd.DataFrame.from_records(path_sheet.rows)

    def get_which_entry_input(self, sheet, prompt='entry: '):
        path_sheet, df = self.load_path_sheet_dataframe()

        cols = []
        for name in sheet.names:
            if name in df.columns:
                cols.append(name)
            # if name in df[0].iloc[0].keys():
            #     cols.append(name)


        # raise Exception(f'{cols} {sheet.names} {df.columns}')
        if len(cols) == 0:
            _which = vd.input(prompt)
        else:
            _which = cols[0]

        return path_sheet, df, _which


    def get_from_to_input(self, sheet):
        path_sheet, df, _from = self.get_which_entry_input(sheet, 'from: ')
        _to = vd.input('to: ')

        return path_sheet, df, _from, _to


    def run_copy(self, sheet):
        path_sheet, df, _from, _to = self.get_from_to_input(sheet)

        df[_to] = df[_from]

        with open(path_sheet.sheet.source.given, 'w') as f:
            jsn = json.dumps(df.to_dict('records'))
            f.write(jsn)

        # vd.view(df.to_dict('records'))
        # Common.sheet_update_cells(path_sheet, df.to_dict('records'))
    
    def run_remove(self, sheet):
        path_sheet, df, entry = self.get_which_entry_input(sheet)

        df = df.drop(entry, axis=1)

        with open(path_sheet.sheet.source.given, 'w') as f:
            jsn = json.dumps(df.to_dict('records'))
            f.write(jsn)


    def run_move(self, sheet):
        path_sheet, df, _from, _to = self.get_from_to_input(sheet)

        df[_to] = df[_from]
        df = df.drop(_from, axis=1)

        with open(path_sheet.sheet.source.given, 'w') as f:
            jsn = json.dumps(df.to_dict('records'))
            f.write(jsn)

    def clear_blacktracker_values(self, df_bt) -> Tuple[int, pd.DataFrame]:
        df_bt_t = df_bt.T
        df_result_t = df_bt_t.copy()
        modified = 0

        for r in df_bt_t:
            v_gcode = df_bt_t[r]['gcode']

            if v_gcode == 'DSUM':
                for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                    lst = df_result_t[r][day].copy()
                    df_result_t[r][day] = [0, 0, lst[2], 0.0, '']
                    modified += 1

                if 'WSUM' in df_bt_t[r]:
                    lst = df_result_t[r]['WSUM'].copy()
                    df_result_t[r]['WSUM'] = [0, 0, lst[2], 0.0, '']
                    modified += 1
            else:
                for day in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                    lst = df_result_t[r][day].copy()
                    df_result_t[r][day] = [0, lst[1], 0, '']
                    modified += 1
                
                # process total column as row sum (+)
                if 'WSUM' in df_bt_t[r]:
                    lst = df_result_t[r]['WSUM'].copy()
                    df_result_t[r]['WSUM'] = [0, 0, lst[2], 0.0, '']
                    modified += 1

                
        result = df_result_t.T

        return (modified, result)

    def load_dataframe(self, sheet, check_sheet=False):
        df_bt = pd.DataFrame.from_records(sheet.rows)
        if not is_valid_blocktracker_df(df_bt):
            if check_sheet: return (None, None)
            raise SelectCommand.Error(f'Invalid BlockTracker sheet {sheet.name}')
        
        return df_bt
    
    def run_clear(self, sheet):
        df_bt = self.load_dataframe(sheet)
        modified, df_bt = self.clear_blacktracker_values(df_bt)
        Common.sheet_update_cells(sheet, df_bt.to_dict('records'))
    
    def run_cust(self, sheet):
        path_sheet, df, entry = self.get_which_entry_input(sheet)

        records = df[entry][0]
        new_records = []

        def rename():
            for record in records:
                new_record = record.copy()

                new_record['WSUM'] = new_record['+']
                del new_record['+']

                if new_record['gcode'] == 'TOT0':
                    new_record['gcode'] = 'DSUM'

                new_records.append(new_record)

        def increase_wsum_elements():
            for record in records:
                new_record = record.copy()

                if new_record['gcode'] != 'DSUM':
                    lst = new_record['WSUM']
                    new_record['WSUM'] = [lst[0], lst[1], 0, lst[2], lst[3]]
                
                new_records.append(new_record)
        
        def reorder_column():
            for record in records:
                new_record = record.copy()
                # del new_record['gcode']
                # del new_record['pri']
                # del new_record['WSUM']
                # new_record = {'gcode': record['gcode'], 'pri': record['pri'], 'WSUM': record['WSUM'], 
                #               **new_record}

                col = 'pri'
                del new_record[col]
                new_record = {col: record[col], **new_record}

                new_records.append(new_record)

        # rename()
        # increase_wsum_elements()
        reorder_column()

        df[entry][0] = new_records
        # df[entry, 0] = new_records
        vd.status(f'type: {type(new_records)}')
        # vd.view(new_records)

        with open(path_sheet.sheet.source.given, 'w') as f:
            jsn = json.dumps(df.to_dict('records'))
            f.write(jsn)


class ScheduleOperations(SelectCommand):
    def __init__(self, key: str, exec=['clear', 'clearActual']):
        self._key = key
        self.exec = exec

    def key(self) -> str: return self._key

    def name(self) -> str: 
        if 'clear' in self.exec: return 'Schedule.Clear'
        if 'clearActual' in self.exec: return 'Schedule.ClearActual'
        raise SelectCommand.Error('No command to execute')

    def help(self) -> str: 
        if 'clear' in self.exec: return 'Clears all cells in scheudle entry'
        if 'clearActual' in self.exec: return 'Clears all non-planned cells in scheudle entry'
        raise SelectCommand.Error('No command to execute')

    def run(self, sheet):
        if 'clear' in self.exec: return self.run_clear(sheet)
        if 'clearActual' in self.exec: return self.run_clear_actual(sheet)
        raise SelectCommand.Error('No command to execute')
    
    def load_df(self, sheet, check_sheet=False):
        # rows = []
        # with open('/tmp/debug.tmp', 'w') as f:
        #     for r, row in enumerate(sheet.rows):
        #         rows.append({'HA': row['HA'], 'A000': row['A000'], 'A020': row['A020'], 'A040' : row['A040'], 'A100': row['A100'], 'A120': row['A120'], 'A140': row['A140'], '    ': '',
        #                      'HP': row['HP'], 'P000': row['P000'], 'P020': row['P020'], 'P040' : row['P040'], 'P100': row['P100'], 'P120': row['P120'], 'P140': row['P140'],
        #                     })
        #         f.write(f'{r}: {rows[r]}\n')

        df_sch = pd.DataFrame.from_records(sheet.rows)
        # df_sch = pd.read_json(json.dumps(sheet.rows))
        # df_sch = pd.DataFrame(sheet.rows)
        
        if not is_valid_schedule_df(df_sch):
            if check_sheet: return (None, None)
            raise SelectCommand.Error(f'Invalid Schedule sheet {sheet.name}')

        # try:
        #     path_sheet = vd.sheets | pipe.where(Common.is_path_sheet) | Pipe(next)
        # except StopIteration:
        #     raise SelectCommand.Error('Could not find path sheet')
        
        # df_schs = pd.read_json(path_sheet.source.given)

        # weekdatecode = sheet.xls_name
        # if weekdatecode not in df_schs:
        #     raise SelectCommand.Error(f'Could not find schedule weekdatecode {weekdatecode}')
        
        # df_sch = pd.DataFrame(df_schs[weekdatecode][0])
        # if not is_valid_schedule_df(df_sch):
        #     raise SelectCommand.Error('Invalid Scheduler json data')
        
        return df_sch
    
    def clear_sch_df(self, df_sch: pd.DataFrame, actual=False) -> pd.DataFrame:
        df_sch_t = df_sch.T
        df_result = df_sch.copy()

        for r in df_sch_t:
            # extract values at specific time period r
            v_HA = df_sch_t[r]['HA'].strip()
            v_HP = df_sch_t[r]['HP'].strip()
            c_A = ['A000', 'A020', 'A040', 'A100', 'A120', 'A140']
            c_P = ['P000', 'P020', 'P040', 'P100', 'P120', 'P140']
            # v_A = [df_sch_t[r]['A000'], df_sch_t[r]['A020'], df_sch_t[r]['A040'], 
            #        df_sch_t[r]['A100'], df_sch_t[r]['A120'], df_sch_t[r]['A140'], ]
            # v_P = [df_sch_t[r]['P000'], df_sch_t[r]['P020'], df_sch_t[r]['P040'], 
            #        df_sch_t[r]['P100'], df_sch_t[r]['P120'], df_sch_t[r]['P140'], ]

            # ensure HA and HP are always identical
            if v_HA != v_HP:
                raise SelectCommand.Error(
                    f'Expected HA and HP to be identical: "{v_HA}" != "{v_HP}"')

            # skip timeless entries
            if v_HA == '':
                continue

            # parse v_HA time and day
            _t = int(v_HA[:-1])
            d = v_HA[-1]

            if d not in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
                raise SelectCommand.Error(f'Expected valid day code for {d}')
            
            erase_list = c_A if actual else c_A + c_P

            for c in erase_list:
                df_result.loc[r, c] = '----'
        
        return df_result
                
    def run_clear(self, sheet: TableSheet):
        df_sch = self.load_df(sheet)

        df_sch = self.clear_sch_df(df_sch)

        # records = df_sch.to_dict('records')
        # with open('/tmp/lol.json', 'w') as f:
        #     f.write(json.dumps(records))

        modified = Common.sheet_update_cells(sheet, df_sch.to_dict('records'))
        vd.status(f'Updated {modified} entries')

    def run_clear_actual(self, sheet: TableSheet):
        df_sch = self.load_df(sheet)

        df_sch = self.clear_sch_df(df_sch, actual=True)

        # records = df_sch.to_dict('records')
        # with open('/tmp/lol.json', 'w') as f:
        #     f.write(json.dumps(records))

        modified = Common.sheet_update_cells(sheet, df_sch.to_dict('records'))
        vd.status(f'Updated {modified} entries')




schedule_json = '/home/lan/.task/schedule/23XXXX/schedule.json'

commands = [
    BlockTrackerAutoCompute('bt', schedule_json, exec=['autocompute']),
    BlockTrackerAutoCompute('bt.i', schedule_json, exec=['view_inverted']),
    BlockTrackerFileSystem('bt.rm', exec=['remove']),
    BlockTrackerFileSystem('bt.cp', exec=['copy']),
    BlockTrackerFileSystem('bt.mv', exec=['move']),
    BlockTrackerFileSystem('bt.clr', exec=['clear']),
    BlockTrackerFileSystem('bt.cust', exec=['cust']),

    BlockTrackerFileSystem('sch.rm', exec=['remove']),
    BlockTrackerFileSystem('sch.cp', exec=['copy']),
    BlockTrackerFileSystem('sch.mv', exec=['move']),
    ScheduleOperations('sch.clr', exec=['clear']),
    ScheduleOperations('sch.clra', exec=['clearActual']),
]
