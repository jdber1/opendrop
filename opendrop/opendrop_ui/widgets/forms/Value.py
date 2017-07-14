from Frame import Frame

from opendrop.utility.events import Event

class Value(Frame):
    """
        Just a convenience class, stores a value of any type, and is included in the dict generated
        by FormWidget.submit()
    """
    def __init__(self, master, name = None, **options):
        Frame.__init__(self, master, name)

        self.value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if not hasattr(self, "on_change"):
            self.on_change = Event()

        self._value = new_value
        self.on_change.fire(new_value)
