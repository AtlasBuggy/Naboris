
from atlasbuggy.datastream import DataStream

class UIstream(DataStream):
    def __init__(self, name, enabled, debug, threaded):
        super(UIstream, self).__init__(name, enabled, debug, threaded)
