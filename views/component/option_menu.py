import tkinter as tk
from utils.config import *

class OptionMenu():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, width_specify=15, label_width=None):
        self.entry_list = options_list
        self.label = tk.Label(
            frame, text=text_left, background=BACKGROUND_COLOR, width=label_width, anchor="w")
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)

        self.optionmenu = tk.OptionMenu(
            *(frame, self.text_variable) + tuple(self.entry_list))
        self.optionmenu.config(bg=BACKGROUND_COLOR, width=width_specify)
        self.optionmenu.grid(row=rw, column=1, sticky="w")

    def get_value(self):
        return self.text_variable.get()

    def set_value(self, value):
        if value in self.entry_list:
            self.text_variable.set(value)
        else:
            self.text_variable.set(self.entry_list[0])

    def disable(self):
        self.optionmenu.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.optionmenu.config(state="normal")
        self.label.config(state="normal")