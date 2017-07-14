from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk
from opendrop.shims import ttk_ as ttk
import tkFileDialog
import tkFont

from opendrop.utility.argfiddler import ExtKwargs

class DirectoryEntry(FormWidget, tk.Frame):
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        tk.Frame.__init__(self, master)
        self.columnconfigure(0, weight = 1)
        self._value = tk.StringVar()
        self._bind_var(self._value)

        self.visible_text = tk.StringVar()
        self.visible_text.set("< No Directory Selected >")
        self.entry = tk.Label(self, textvariable = self.visible_text, anchor = "w")#state = "readonly")
        self.entry.grid(row = 0, column = 0, sticky = "we")

        self.button = ttk.Button(self,
            text = "Browse",
            command = self.update_directory
        )
        self.button.grid(row = 0, column = 2, sticky = "e")
        self.configure(**options)

    def _configuration_dump(self):
        return self.entry.configure() # Not fully implemented

    def configure(self, **options):
        assert(self.entry and self.button)

        if not options:
            return self._configuration_dump()

        options = ExtKwargs(options)
        options.alias({"background":"bg"})

        frame_options = options.extract("background", "padx", "pady")
        tk.Frame.configure(self, **frame_options)

        entry_options = options.extract("font", "width", "background") #\
                               #.rename({"background": "highlightbackground"})
        self.entry.configure(**entry_options)

        button_options = options.extract("button_width") \
                                .rename({"button_width": "width"})
        self.button.configure(**button_options)

    @property
    def value(self):
        return self._value.get()

    @value.setter
    def value(self, value):
        self._value.set(value)
        self.set_visible_text(value)

    def set_visible_text(self, actual_value):
        entry_width = self.entry.winfo_width()
        entry_font = tkFont.Font(font = self.entry["font"])

        if entry_font.measure(actual_value) < entry_width:
            self.visible_text.set(actual_value)
        else: # Text too long, won't fit, need to trim. Kind of hacky but it works
            ellipsis_width = entry_font.measure("...")
            available_width = float(entry_width * 0.95 - ellipsis_width)
            # *0.95 just to give it a bit of leeway so the text doesn't overshoot a tiny amount

            clipped_value = None
            next_clipped_value = actual_value

            # Keep changing the string length to match available_width until steady state reached
            while clipped_value is None or abs(len(next_clipped_value) - len(clipped_value)) > 1:
                # print(clipped_value, next_clipped_value)
                clipped_value = next_clipped_value


                clipped_text_width = float(entry_font.measure(clipped_value))
                avg_char_width = clipped_text_width/len(clipped_value)
                # print(clipped_text_width, avg_char_width)

                clipped_text_len = available_width/avg_char_width
                # assert(clipped_text_len < len(actual_value))

                next_clipped_value = actual_value[-int(round(clipped_text_len)):]
            # print(entry_width, available_width, entry_font.measure(clipped_value))
            self.visible_text.set("..." + clipped_value)

    def update_directory(self):
        initialdir = self.value

        new_dir = tkFileDialog.askdirectory(
            parent = self,
            initialdir = initialdir,
            title = "Select output data location"
        )

        if new_dir:
            self.value = new_dir
