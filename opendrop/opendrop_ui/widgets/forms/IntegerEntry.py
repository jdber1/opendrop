from TextEntry import TextEntry

from opendrop.shims import tkinter_ as tk

class IntegerEntry(TextEntry):
    def __init__(self, master, **options):
        TextEntry.__init__(self, master, **options)

        self.configure_(
            validate = "key",
            validatecommand = (
                master.register(IntegerEntry.validate),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"
            )
        )

    @property
    def value(self):
        return int(super(IntegerEntry, self).value or "0")

    @value.setter
    def value(self, value):
        # Ugh, this is a reall messy way of setting an inherited property, this is because super()
        # only works with getters and doesnt work with __set__ in descriptors. We need to use this
        # functionality since we are overriding the 'value' setter/getters with our own wrapper that
        # first converts values to integers.
        super(IntegerEntry, IntegerEntry).value.__set__(self, int(value or "0"))

    @classmethod
    def validate(cls, action, index, value_if_allowed, prior_value, text, validation_type,
                 trigger_type, widget_name):
        if value_if_allowed == '':
            return True
        elif value_if_allowed == '0':
            return False
        else:
            if text in '0123456789':
                try:
                    int_value = int(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False
