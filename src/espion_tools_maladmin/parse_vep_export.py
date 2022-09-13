"""
Code to parse an espion VEP export file
"""

import logging
import codecs
from espion_objects import TimeSeries, Result, StepChannel, Step, FileError
from utils import as_int, as_float, parse_dateTimeStamp, parse_dateStamp
logger = logging.getLogger(__name__)


def load_file(filepath):
    """
    Load an espion export file, check it's in the correct format.
    Returns a file object or raises a FileError exception.
    """
    #with open(filepath, 'r') as f:
    with codecs.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        line = f.readline()
        if not line.strip().split('\t')[0] == 'Contents Table':
            raise FileError
    return f

def move_top(f, lines):
    """
    Takes an open file and moves to the start of lines
    """
    f.seek(0)
    for i in range(lines - 1):
        f.readline()

def parse_contents(f, sep):
    """
    Read the contents table from an espion export file.
    Returns a dict with the contents
    """
    logger.debug('Parsing contents')
    start_str = 'Contents Table'
    contents_table = {}

    # skip the next two lines, not important
    f.readline()
    f.readline()
    f.readline()
    while True:
        line = f.readline()
        line = line.split(sep)
        if line[0] == '':
            break
        contents_table[line[0]] = {'left': as_int(line[1]),
                                   'top': as_int(line[2]),
                                   'right': as_int(line[3]),
                                   'bottom': as_int(line[4])}
    return contents_table

def parse_header_section(f, contents, sep):
    logger.debug('Parsing header table')
    if not 'Header Table' in contents.keys():
        raise FileError

    headers = {}

    locations = contents['Header Table']
    # scroll to the top of the section
    
    
    #version problem 
    #version 6.0.56 has headers Group, Name, Hosp#, DOB, Date
    #version 6.64.14 has headers Group, Name, Hosp#, Age, Date, Comment
    move_top(f, locations['top'])

    while True:
        line = f.readline()
        line = line.split(sep)
        values = line[locations['left']-1:locations['right']]
        if ''.join(values) == '':
            break
        logger.debug('header:{}  {}'.format(values[0], values[1]))
        headers[values[0]] = values[1]

    for header in headers:
        if header == 'Date performed':
            headers[header] = parse_dateTimeStamp(headers[header])
        elif header in ('Steps', 'Channels'):
            headers[header] = as_int(headers[header])
        elif header == 'DOB':
            headers[header] = parse_dateStamp(headers[header])

    return(headers)

def parse_marker_section(f, contents, sep, version):
    def read_old_marker_line():
        if has_norms:
            marker = {'chan':as_int(values[6]),
                      'result':values[7],
                      'eye':values[8],
                      'name':values[9],
                      'amp':as_float(values[10]),
                      'amp_norm':values[11],
                      'time':as_float(values[12]),
                      'time_norm':values[13]}
        else:
            marker = {'chan':as_int(values[6]),
                      'result':values[7],
                      'eye':values[8],
                      'name':values[9],
                      'amp':as_float(values[10]),
                      'time':as_float(values[11])}
        return(marker)
    
    def read_new_marker_line():
        if has_norms:
            marker = {'chan':as_int(values[7]),
                      'result':values[8],
                      'eye':values[9],
                      'name':values[10],
                      'amp':as_float(values[11]),
                      'amp_norm':values[12],
                      'time':as_float(values[13]),
                      'time_norm':values[14]}
        else:
            marker = {'chan':as_int(values[7]),
                      'result':values[8],
                      'eye':values[9],
                      'name':values[10],
                      'amp':as_float(values[11]),
                      'time':as_float(values[12])}
        return(marker)
        
    logger.debug('Parsing marker table')
    if not 'Marker Table' in contents.keys():
        raise FileError

    markers = {}

    locations = contents['Marker Table']
    move_top(f, locations['top'])

    

    if locations['right'] - locations['left'] == 13:
        has_norms = True
    else:
        has_norms = False

    while True:
        line = f.readline()
        line = line.split(sep)
        values = line[locations['left']-1:locations['right']]
        if ''.join(values) == '':
            break

        if version:
            step_no = int(values[6])
            if locations['right'] - locations['left'] == 13:
                has_norms = True
            else:
                has_norms = False
        else:
            step_no = int(values[5])
            if locations['right'] - locations['left'] == 14:
                has_norms = True
            else:
                has_norms = False

        if version:
            marker = read_new_marker_line()    
        else:
            marker = read_old_marker_line()


        if marker['result'].endswith('A'):
            marker['is_average'] = True
            marker['result'] = as_int(marker['result'][0:-1])
        else:
            marker['is_average'] = False
            marker['result'] = as_int(marker['result'])

        if has_norms:
            for key in ['amp_norm', 'time_norm']:
                try:
                    marker[key] = [as_float(val) for val in marker[key].split('+/-')]
                except ValueError:
                    marker[key] = [None, None]

        try:
            markers[step_no].append(marker)
        except KeyError:
            markers[step_no] = []
            markers[step_no].append(marker)

    return(markers)



def parse_summary_table(f, contents, sep):
    logger.debug('Parsing summary table')
    if not 'Summary Table' in contents.keys():
        raise FileError

    steps = {}

    locations = contents['Summary Table']
    move_top(f, locations['top'])

    while True:
        line = f.readline()
        line = line.split(sep)
        values = line[locations['left']-1:locations['right']]
        if ''.join(values) == '':
            break
        step_id = int(values[2])
        step_vals = {'result':int(values[3]),
                     'eye':values[4],
                     'trials':int(values[5]),
                     'rejects':int(values[6]),
                     'comment':values[8]}
        try:
            steps[step_id].append(step_vals)
        except KeyError:
            steps[step_id] = [step_vals]

    return steps

def parse_stimulus_table(f, contents, sep):
    logger.debug('Parsing stimulus table')
    if not 'Stimulus Table' in contents.keys():
        raise FileError('Stimulus table not found')

    stimuli = {}

    locations = contents['Stimulus Table']
    move_top(f, locations['top'])

    while True:
        line = f.readline()
        line = line.split(sep)
        values = line[locations['left']-1:locations['right']]
        if ''.join(values) == '':
            break
        step_id = int(values[0])
        step_vals = {'description': values[1],
                     'stim': values[2]}
        stimuli[step_id] = step_vals

    return stimuli

def parse_data_table(f, contents, sep, summary_table):
    """
    Read the data table.
    Does this by reading an entire line then splitting the values and appending 
    them to the individual trials.
    done this way so we only loop through the file once instead of
    once per trial
    """
    logger.debug('Parsing data table')
    if not 'Data Table' in contents.keys():
        raise FileError('Data table not found')

    data = {}
    # data will end up with structure
    # step
    #    channel
    #        result
    #            trials

    locations = contents['Data Table']
    move_top(f, locations['top'])

    # parse the data summary table to find locations for the trials etc.
    while True:
        line = f.readline()
        line = line.split(sep)
        # ERG step summary info has 5 columns
        values = line[locations['left']-1:locations['left'] + 5]
        if ''.join(values) == '':
            break

        step_no = int(values[0])
        step_col = int(values[1])
        chan_no = int(values[2])
        result_no = int(values[3])
        result_col = int(values[4])
        trial_count = int(values[5])

        # If a trial has been excluded from a single channel the result count
        # in this table can be incorrect. 


        try:
            data[step_no].add_channel(chan_no)
        except KeyError:
            data[step_no] = Step(step_no)
            data[step_no].add_channel(chan_no)

        if not data[step_no].column:
            # this number is only valid for the first channel in a step
            data[step_no].column = step_col

        logger.debug('Adding result: {} to channel:{} of step:{}'
                     .format(result_no, chan_no, step_no))
        try:
            data[step_no].channels[chan_no].results[result_no].column = result_col
        except KeyError:
            data[step_no].channels[chan_no].add_result(result_no)
            data[step_no].channels[chan_no].results[result_no].column = result_col

        data[step_no].channels[chan_no].results[result_no].trial_count = trial_count

    # start reading the real data
    move_top(f, locations['top'] - 1)
    # trial count value can be incorrect if a trial has been excluded from a 
    # single channel. Going to capture the header column to ensure we are looking at 
    # the correct column.
    headers = f.readline()
    headers = headers.split(sep)

    # need firt two lines to determine timeseries parameters
    line_one = f.readline()
    line_one = line_one.split(sep)
    line_two = f.readline()
    line_two = line_two.split(sep)

    for step_id, step in data.items():
        time_start = float(line_one[step.column - 1])
        time_delta = float(line_two[step.column - 1]) - time_start
        for channel_id, channel in step.channels.items():
            for result_id, result in channel.results.items():
                result.data = TimeSeries(time_start, time_delta)
                result.data.values.append(float(line_one[result.column - 1]))
                result.data.values.append(float(line_two[result.column - 1]))

                for trial_no in range(result.trial_count):
                    if headers[result.column + trial_no] != 'Trial (nV)':
                        result.trial_count = trial_no
                        break
                    result.trials.append(TimeSeries(time_start, time_delta))
                    result.trials[trial_no].values.append(float(line_one[result.column + trial_no]))
                    result.trials[trial_no].values.append(float(line_two[result.column + trial_no]))

    while True:
        values = f.readline()
        values = values.split(sep)
        if ''.join(values) == '':
            break
        for step_id, step in data.items():
            for channel_id, channel in step.channels.items():
                for result_id, result in channel.results.items():
                    if values[result.column - 1] == '':
                        # have a problem here if a subsequent step has a longer time series
                        continue
                    result.data.values.append(float(values[result.column - 1]))

                    for trial_no in range(result.trial_count):
                        result.trials[trial_no].values.append(float(values[result.column + (trial_no)]))
    return(data)

def read_export_file(filepath, sep='\t'):
    logger.debug('Reading file:{}'.format(filepath))
    #with open(filepath, 'r') as f:
    with codecs.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        line = f.readline()
        if not line.strip().split(sep)[0] == 'Contents Table':
            raise FileError
        f.seek(0)
        contents = parse_contents(f, sep)
        header = parse_header_section(f, contents, sep)
        markers = parse_marker_section(f, contents, sep, header.get('Version'))
        summary = parse_summary_table(f, contents, sep)
        stimuli = parse_stimulus_table(f, contents, sep)
        data = parse_data_table(f, contents, sep, summary)
    return({'contents':contents,
            'headers':header,
            'markers':markers,
            'summary':summary,
            'stimuli':stimuli,
            'data':data})


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    filepath = "../../samples/erg_protocol_1.2_version_6.64.14.txt"
    read_export_file(filepath)
