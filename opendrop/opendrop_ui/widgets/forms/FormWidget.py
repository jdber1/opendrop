from opendrop.shims import tkinter_ as tk

from opendrop.utility.events import Event

class FormWidget(tk.Frame, object):
    """
        Base class for all form widgets.

        Attributes:
            value: The value that represents this widget
            state: The state of the widget, "normal" or "disabled"
            on_change: If _bind_var(var) has been called, this attribute is a utility.events.Event
            object that is fired whenever 'var' is changed
        Methods:
            submit(): Returns a dict that contains the values of children with value attributes with
            the keys being their name attribute. If the child has no value but contains children,
            then the returned dict will be nested.
            disable(): Disable the widget
            normal(): Enable the widget
            _bind_var(var): When inheriting FormWidget to create custom widgets, call
            self._bind_var(var), with 'var' being a Tkinter variable. This will hook the 'on_change'
            event onto this variable and the event will fire everytime the variable is changed
    """
    def __init__(self, parent, name):
        self.name = name

    def submit(self):
        form = {}

        for child in self.winfo_children():
            if isinstance(child, FormWidget) and child.name:
                try:
                    form[child.name] = child.value
                except AttributeError:
                    form[child.name] = child.submit()

        return form

    def find_child_by_name(self, name):
        for child in self.winfo_children():
            if isinstance(child, FormWidget):
                if child.name == name:
                    return child

    def update(self, data):
        for k, v in data.items():
            child = self.find_child_by_name(k)

            if isinstance(v, dict):
                child.update(v)
            else:
                child.value = v

    # TODO: AUTO DETECT VALUE TYPE AND DO STUFF, change 'on_change' to .change
    @property
    def value(self):
        if hasattr(self, "_value"):
            return self._value.get()
        else:
            raise AttributeError

    @value.setter
    def value(self, value):
        if hasattr(self, "_value"):
            return self._value.set(value)
        else:
            raise AttributeError

    @property
    def state(self):
        return self.configure()["state"][-1]

    def configure(self, *args, **kwargs):
        try:
            return self.configure_(*args, **kwargs)
        except:
            raise NotImplementedError

    def config(self, *args, **kwargs):
        return self.configure(*args, **kwargs)

    def disable(self):
        self.configure(state = "disabled")

    def normal(self):
        self.configure(state = "normal")

    def _bind_var(self, var):
        self.on_change = Event()

        def cb(*args, **kwargs):
            self.on_change.fire(self, self.value)

        var.trace("w", cb)

        self._value = var
