from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk

from opendrop.utility.argfiddler import ExtKwargs
#default width 15
class OptionMenu(FormWidget, tk.OptionMenu):
    def __init__(self, master, values, name = None, **options):
        FormWidget.__init__(self, master, name)

        self._value = tk.StringVar()
        self._bind_var(self._value)

        tk.OptionMenu.__init__(self, master, self._value, *values)

        self.values = values

        self.configure(**options)

    def _configuration_dump(self):
        return self.configure_() # Not fully implemented

    configure_ = tk.OptionMenu.configure
    def configure(self, *args, **kwargs):
        try:
            return self.configure_(self, *args, **kwargs)
        except:
            if not kwargs:
                return self._configuration_dump()

            options = ExtKwargs(kwargs)
            options.alias({"background":"bg"})

            option_menu_config_options = options.extract("font", "width", "height", "background",
                                                         "state")
            self.configure_(**option_menu_config_options)

            option_menu_font_options = options.extract("font")
            self.nametowidget(self.menuname).configure(
                **option_menu_font_options
            )

    @property
    def value(self):
        return self._value.get()

    @value.setter
    def value(self, value):
        if value in self.values:
            self._value.set(value)
        else:
            self._value.set(self.values[0])
