# -*- coding: utf-8 -*-
"""
Code to parse an espion export file
"""
from .exceptions import EspionExportError
from .parse_vep_export import read_export_file
from .parse_mferg_export import read_mferg_export_file
import logging
import codecs

logger = logging.getLogger(__name__)

def find_type(fpath):
    """
    Reads an espion export file and determines if it is an mfERG or VEP/ERG
    export format.
    Returns a dict {'type': 'vep'|'mferg',
                    'test': 'erg'|'mferg'|'vep',
                    'sep': '\t'|','|' '|';'|':'}
    """
    separators = {'tab': '\t',
                  'comma': ',',
                  'semi': ';',
                  'colon': ':'}
    export_type, sep = None, None
    
    #with open(fpath, 'r') as f:
    with codecs.open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        line = f.readline()
        for key in separators:
            if separators[key] in line:
                sep = separators[key]
                break
        if not sep:
            sep = ' '
        
        if line.split(sep)[0].strip() == 'Contents Table':
            export_type = 'vep'
        elif line.split(sep)[0].strip() == 'Parameter':
            export_type = 'mferg'
        else:
            raise EspionExportError('Unknown Type')
            
        if export_type == 'mferg':
            test_type = 'mferg'
        else:
            while True:
                line = f.readline()
                line = line.split(sep)
                line = [value.strip() for value in line]
                if 'Test method' in  line:
                    test_type = line[line.index('Test method') + 1]
                    if test_type == 'VEP Test':
                        test_type = 'vep'
                    elif test_type == 'ERG Test':
                        test_type = 'erg'
                    else:
                        raise EspionExportError('Test type:{} is not recognised'
                                                .format(test_type))
                    break
                    
            
    return({'type': export_type,
            'test_type': test_type,
            'sep': sep})
        
def load_file(fpath):
    """
    Parses an espion export file
    returns ['type': 'mferg'|'vep',
             'data': file contents]
    or raises an EspionExportError
    """
    info = find_type(fpath)
    try:
        if info['type'] == 'mferg':
            data = read_mferg_export_file(fpath, sep=info['sep'])
        else:
            data = read_export_file(fpath, sep=info['sep'])
    except:
        raise EspionExportError('Invalid file format:{}'.format(fpath))
    return([info, data])
    
