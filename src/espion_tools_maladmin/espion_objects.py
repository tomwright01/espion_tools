import logging

logger = logging.getLogger(__name__)
class FileError(Exception):
    """
    Invalid export file.
    """


class TimeSeries():
    def __init__(self, start, delta, values=[]):
        self.start = start
        self.delta = delta
        self.values = []
        if values:
            self.values = values

class Result():
    def __init__(self, result_number):
        self.result_number = result_number
        self.data = None
        self.trials = []
        self.column = None
        self.trial_count = 0

class StepChannel():
    def __init__(self, channel_number):
        assert int(channel_number) > 0, 'Invalud channel number'
        self.channel_number = channel_number
        self.result_count = 0
        self.results = {}

    def add_result(self, result_number):
        if result_number not in self.results.keys():
            self.results[result_number] = Result(result_number)

class Step():
    def __init__(self, step_number):
        assert int(step_number) > 0, 'Invalid step number'
        self.description = ''
        self.stim = ''
        self.step_number = step_number
        self.channels = {}
        self.column = None

    def add_channel(self, channel_id):
        if channel_id not in self.channels.keys():
            self.channels[channel_id] = StepChannel(channel_id)

class Mferg():
    def __init__(self):
        self.hexagons = []

class Hexagon():
    def __init__(self, eye, hex_id):
        self.hex_id = hex_id
        self.eye = eye
        self.n1 = (None, None)
        self.p1 = (None, None)
        self.data_raw = None
        self.data_smooth = None
