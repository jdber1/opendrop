from opendrop.utility.events import EventSource
from opendrop.utility.events.events import HasEvents


class Model(HasEvents):
    def __init__(self):
        self.events = EventSource()
