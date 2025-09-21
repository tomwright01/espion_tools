from datetime import datetime

def as_int(val):
	"""
	Tries to convert a string to an int.
	Returns None if string is empty
	"""
	try:
		return(int(val))
	except ValueError:
		return(None)

def as_float(val):
	"""
	Tries to convert a string to an float.
	Returns None if string is empty
	"""
	try:
		return(float(val))
	except ValueError:
		return(None)

def read_split_line(f, split='\t', start_col=None):
    line = f.readline()
    line = line.split(split)
    if start_col:
        line = line[start_col:]
    return line

def find_section_col(values, strings, start = 0):
    """
    returns the index in values that matches strings or None
    Note index is from start of values, not the start parameter
    if strings is a list returns the index where multiple columns match
    >>> find_section_col(['Hexagon','','Hexagon','X'],'Hexagon')
    0
    >>> find_section_col(['Hexagon','','Hexagon','X'],['Hexagon','X'])
    2
    >>> find_section_col(['Hexagon','','Hexagon','X'],'Not a hexagon')
    None
    """
    if not isinstance(strings, list):
        strings = [strings]
        
    values = values[start:]
    
    try:
        col = values.index(strings[0])
    except ValueError:
        return None
    
    for i,v in enumerate(strings):
        if not values[col + i] == v:
            col = find_section_col(values, strings, col + 1)
    
    try:
        col = col + start
    except TypeError:
        col = None
    
    return col

def parse_dateTimeStamp(str):
    """

    Parameters
    ----------
    str : DateTime data
        Parse a timestamp string

    Returns
    -------
    DateTime object.

    """
    try:
        ts = datetime.strptime(str, '%m/%d/%Y  %I:%M:%S %p')
    except ValueError:
        ts = datetime.strptime(str, '%Y-%m-%d  %I:%M:%S %p')
    
    return(ts)

def parse_dateStamp(str):
    """

    Parameters
    ----------
    str : Date string
        Parse a timestamp string

    Returns
    -------
    Date object.
    """
    try:
        ts = datetime.strptime(str, '%m/%d/%Y')
    except ValueError:
        ts = datetime.strptime(str, '%Y-%m-%d')    
        
    return(ts)