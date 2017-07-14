from opendrop.shims import ttk_ as ttk

from opendrop.utility.argfiddler import ExtKwargs

class Button(ttk.Button):
    def __init__(self, master, **options):
        ttk.Button.__init__(self, master)

        self.configure(**options)

    configure_ = ttk.Button.configure
    def configure(self, **options):
        options = ExtKwargs(options)

        options = options.extract("width", "height", "text", "command")
        return self.configure_(**options)
