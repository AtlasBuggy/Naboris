
from atlasbuggy.datastream import DataStream

class IOstream(DataStream):
    def __init__(self, stream_name, debug):
        super(IOstream, self).__init__("IOstream > " + stream_name, debug)

