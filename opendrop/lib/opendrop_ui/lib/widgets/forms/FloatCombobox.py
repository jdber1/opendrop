from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk
from opendrop.shims import ttk_ as ttk

from opendrop.utility.argfiddler import ExtKwargs

class FloatCombobox(FormWidget, ttk.Combobox):
    """
        Combobox with float type options, also allows manual input of a value not in options.

        Args:
            text(str): Text of label that appears on the left of the combobox
            values(list(str)): A list of floats formatted as strings of the available options
            width(int): Width of the combobox (excluding label width)
            label_width(int): Width of the label

        Methods:
            disable(): Disables the widget
            normal(): Enables the widget
    """
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        self._value = tk.StringVar()
        self._bind_var(self._value)

        ttk.Combobox.__init__(self, master,
            textvariable = self._value,
            validate = "key",
            validatecommand = (
                 master.register(FloatCombobox.validate),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"
            ),
        )

        self.configure(**options)

    def _configuration_dump(self):
        return self.configure_() # Not fully implemented

    configure_ = ttk.Combobox.configure
    def configure(self, **options):
        if not options:
            return self._configuration_dump()

        options = ExtKwargs(options)
        options.alias({"background":"bg"})

        combobox_config_options = options.extract("font", "width", "state", "values")
        self.configure_(**combobox_config_options)

    @classmethod
    def validate(cls, action, index, value_if_allowed, prior_value, text, validation_type,
                 trigger_type, widget_name):
        if value_if_allowed == "":
            return True
        elif value_if_allowed == ".":
            return True
        else:
            if text in "0123456789.-+":
                try:
                    float(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False

    @property
    def value(self):
        return float(self._value.get() or "0")

    @value.setter
    def value(self, value):
        self._value.set(str(float(value)))
