"""
Code to parse an espion mferg export file
"""
from datetime import datetime
import logging
import re
from .espion_objects import TimeSeries, FileError, Hexagon
from .utils import as_int, as_float, read_split_line, find_section_col

logger = logging.getLogger(__name__)

def move_top(f, lines):
    """
    Takes an open file and moves to the start of lines
    """
    f.seek(0)
    for i in range(lines - 1):
        f.readline()

def parse_parameters(f, sep):
    logger.debug('Parsing parameters')
    parameters = {}
    move_top(f, 2)
    while True:
        line = f.readline()
        line = line.split(sep)
        if line[0] == '':
            break
        parameters[line[0]] = line[1]
    for parameter in parameters:
        if parameter in ['Test Date', 'DOB']:
            parameters[parameter] = datetime.strptime(parameters[parameter], '%m/%d/%Y')
        if parameter in ['Hexagons', 'Kernel Order', 'Sequence Bits', 'Filler Frames']:
            parameters[parameter] = as_int(parameters[parameter])

    return parameters

def parse_markers(f, sep):
    logger.debug('Parsing markers')
    hexagons = {}

    move_top(f, 1)
    line = read_split_line(f, split=sep)
    move_top(f, 1)
    start_col = find_section_col(line, 'Hexagon')
    line = read_split_line(f, split=sep, start_col=start_col)
    if line[5] == 'Left Eye':
        # both eyes exported
        binocular = True
    else:
        binocular = False
    if line[1] == 'Left Eye':
        eye = 'os'
    else:
        eye = 'od'
        
    f.readline()
    while True:
        line = read_split_line(f, split=sep, start_col=start_col)
        if line[0] == '':
            break
        hexagon1 = Hexagon(eye, line[0])
        hexagon1.n1 = (line[1], line[2])
        hexagon1.p1 = (line[3], line[4])

        if binocular:
            hexagon2 = Hexagon('os', line[1])
            hexagon2.n1 = (line[5], line[6])
            hexagon2.p1 = (line[7], line[8])
            hexagons[line[0]] = (hexagon1, hexagon2)
        else:
            if eye=='os':
                hexagons[line[0]] = (None, hexagon1)
            else:
                hexagons[line[0]] = (hexagon1, None)
    return hexagons

def parse_dimensions(f, sep):
    logger.debug('Parsing dimensions')
    dimensions = {}
    move_top(f,1)
    line = read_split_line(f, split=sep)
    start_col = find_section_col(line, 'Dimensions')

    while True:
        line = read_split_line(f, split=sep, start_col=start_col)
        if line[0] == '':
            break
        dimensions[line[0]] = as_int(line[1])
    return dimensions

def parse_positions(f, sep):
    logger.debug('Parsing positions')
    locations = {}
    move_top(f,1)
    line = read_split_line(f, split=sep)
    start_col = find_section_col(line, ['Hexagon', 'X'])
    while True:
        line = read_split_line(f, split=sep, start_col=start_col)
        if not line or line[0] == '':
            break
        hex = line[0]
        x_locs = []
        y_locs = []
        x_locs.append(as_float(line[1]))
        y_locs.append(as_float(line[2]))
        for i in range(6):
            line = read_split_line(f, split=sep, start_col=start_col)
            x_locs.append(as_float(line[1]))
            y_locs.append(as_float(line[2]))
        locations[hex] = (x_locs, y_locs)
    logger.debug('Parsed positions')
    return locations

def parse_timeseries(f, hexcount, sep, markers=None):
    """
    Parse time series data, 
    f - file handle
    hexcount - number of hexagons
    sep - file seperator
    [markers] - dict containing hexagon objects
    
    if markers is supplies adds data to existing object otherwise creates
    a new list (not yet implemented)
    """
    logger.debug('Parsing timeseries')
    if not markers:
        markers = {}
    col_head_raw = 'Hex {} (R)'
    col_head_smooth = 'Hex {} (S)'

    eye_strs = {'os': {'str':'Left Eye (nV)'},
                'od': {'str':'Right Eye (nV)'}}
    eye_columns = {}

    move_top(f,1)
    line = read_split_line(f, split=sep)

    for key, val in eye_strs.items():
        eye_idx = find_section_col(line, val['str'])
        if eye_idx:
            eye_columns[key] = eye_idx

    logger.debug('Getting time info')        
    line = read_split_line(f, split=sep)
    time_col = find_section_col(line, 'Time (ms)')
    line = read_split_line(f, split=sep)
    time_1 = as_float(line[time_col])
    line = read_split_line(f, split=sep)
    time_2 = as_float(line[time_col])
    delta = time_2 - time_1
    move_top(f, 2)
    logger.debug('Got time info')
    # find the column indexes for the raw and smooth data
    # going to populate each item (hexagon) in the dict with the column index
    # and a time series object
    line = read_split_line(f, split=sep)
    col_idx_raw = {}
    col_idx_smooth = {}

    for eye, val in eye_columns.items():
        col_idx_raw[eye] = {}
        col_idx_smooth[eye] = {}
        for hex_id in range(hexcount):
            hex_id = hex_id + 1
            col_idx_raw[eye][hex_id] = [find_section_col(line, col_head_raw.format(hex_id), val), 
                                       TimeSeries(start=time_1, delta=delta)]

            col_idx_smooth[eye][hex_id] = [find_section_col(line, col_head_smooth.format(hex_id), val),
                                          TimeSeries(start=time_1, delta=delta)]

    while True:
        line = read_split_line(f, split=sep)
        if line[time_col] == '':
            break
        for hex_id in range(hexcount):
            hex_id = hex_id + 1
            for eye in eye_columns.keys():
                # use the column index to read the data and populate the time series
                if col_idx_raw[eye][hex_id]:
                    col_idx_raw[eye][hex_id][1].values.append(float(line[col_idx_raw[eye][hex_id][0]]))
                if col_idx_smooth[eye][hex_id]:
                    col_idx_smooth[eye][hex_id][1].values.append(float(line[col_idx_smooth[eye][hex_id][0]]))
    data={}
    for eye in ('os','od'):
        if eye in eye_columns.keys():
            data[eye]= {}
            data[eye]['raw'] = {key: val[1] for key, val in col_idx_raw[eye].items()}
            data[eye]['smooth'] = {key: val[1] for key, val in col_idx_smooth[eye].items()}
    logger.debug('Parsed timeseries')
    return(data)

def parse_smooth_string(str):
    """
    Parse an average string from parameters settings
    """
    p = '(Off|Average)(?: \[(.*)])?'
    m = re.match(p, str)
    return(m.groups())

def parse_filter_string(str):
    """
    Parse an filter string from parameters settings
    """
    p = '(Off|Adaptive|FFT)(?: \[(.*)])?'
    m = re.match(p, str)
    return(m.groups())

def parse_luminance_string(str):
    p = '^(\d*)(.*)'
    m = re.match(p, str)
    return(m.groups())

def extract_number(str):
    p = '(\d*)'
    m = re.match(p, str)
    return(m.group(1))


def read_mferg_export_file(filepath, sep='\t'):
    with open(filepath, 'r') as f:
        line = f.readline()
        if not line.strip().split(sep)[0] == 'Parameter':
            raise FileError
        f.seek(0)
        parameters = parse_parameters(f, sep)
        hex_count = as_int(parameters['Hexagons'])
        markers = parse_markers(f, sep)
        dimensions = parse_dimensions(f, sep)
        positions = parse_positions(f, sep)
        data = parse_timeseries(f, hex_count, sep, markers)
        smooth_details = parse_smooth_string(parameters['Smoothing'])
        filter_details = parse_filter_string(parameters['Filtering'])
        lum_on_details = parse_luminance_string(parameters['Luminance On'])
        lum_off_details = parse_luminance_string(parameters['Luminance Off'])
        # do this to make these files similar format to ERG and VEP
        protocol = {'hex_count': parameters['Hexagons'],
                    'scaled': parameters['Scaled'],
                    'distortion': parameters['Distortion'],
                    'filter': parameters['Filter'],
                    'base_period': extract_number(parameters['Base Period']),
                    'correlated': extract_number(parameters['Correlated']),
                    'sequence_len': parameters['Sequence Bits'],
                    'smoothing_type': smooth_details[0].lower(),
                    'smoothing_level': smooth_details[1],
                    'filter_type': filter_details[0].lower(),
                    'filter_level': filter_details[1],
                    'filler_frames': parameters['Filler Frames'],
                    'background': parameters['Background'].lower(),
                    'color_on': parameters['Color On'],
                    'luminance_on': lum_on_details[0],
                    'color_off': parameters['Luminance Off'],
                    'luminance_off': lum_off_details[0],
                    'notch_filter': parameters['Mains Rejection'],
                    'noise_rejection_passess': extract_number(parameters['Noise Rejection']),
                    'description': 'mferg_{}_{}'.format(parameters['Hexagons'],
                                                        parameters['Sequence Bits'])}
    parameters['Protocol'] = 'MfERG_{}'.format(protocol['hex_count'])

    return({'params': parameters,
            'markers': markers,
            'dims': dimensions,
            'positions': positions,
            'data': data,
            'stimuli': protocol})

if __name__=='__main__':
    fname = 'data/mferg-Both Eyes-11.22.2017.TXT'
    read_mferg_export_file(fname)
    import pdb; pdb.set_trace()
