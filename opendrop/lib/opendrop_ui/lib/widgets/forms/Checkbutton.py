from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk

class Checkbutton(FormWidget, tk.Checkbutton):
    """
        Simple Checkbutton

        Methods:
            freeze(): Like .disable() but instead of disabling and setting .value to False, disables
            the widget but retains its current value and prevents user from changing it. To
            'unfreeze', call .normal()
    """
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        self._previous_state = False
        self._value = tk.BooleanVar()
        self._bind_var(self._value)

        tk.Checkbutton.__init__(self, master,
            variable = self._value,
            onvalue = True,
            offvalue = False
        )

        self.configure(**options)

    configure_ = tk.Checkbutton.configure
    def configure(self, onvalue = True, offvalue = False, **options):
        return self.configure_(**options)

    @property
    def value(self):
        return self._value.get()

    @value.setter
    def value(self, value):
        self._value.set(value)

    def disable(self):
        self._previous_state = self.value
        self.value = False
        self.configure(state = "disable")

    def freeze(self):
        self._previous_state = self.value
        self.configure(state = "disable")

    def normal(self):
        self.value = self._previous_state
        self.configure(state = "normal")
