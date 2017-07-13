from TextEntry import TextEntry

from opendrop.shims import tkinter_ as tk

class FloatEntry(TextEntry):
    def __init__(self, master, **options):
        TextEntry.__init__(self, master, **options)

        self.configure_(
            validate = "key",
            validatecommand = (
                master.register(FloatEntry.validate),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"
            )
        )

    @property
    def value(self):
        return float(super(FloatEntry, self).value or "0.0")

    @value.setter
    def value(self, value):
        # Need to use __set__ on a super's attribute, look at IntegerEntry.py for more information
        super(FloatEntry, FloatEntry).value.__set__(self, float(value or "0.0"))


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
