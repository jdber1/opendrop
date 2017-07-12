from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk

from opendrop.utility.argfiddler import ExtKwargs

class LabelFrame(FormWidget, tk.LabelFrame):
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        tk.LabelFrame.__init__(self, master)

        self.configure(**options)

    def configure(self, **options):
        options = ExtKwargs(options).alias({"background":"bg"}) \
                                    .extract("width", "height", "padx", "pady", "background",
                                             "text", "font")
        return tk.Frame.configure(self, **options)
