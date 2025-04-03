import tkinter as tk

from utils.config import *
from utils.validators import *

class IntegerEntry():
    def __init__(self, parent, frame, text_left, callback, rw=0, cl=0, pdx=0, width_specify=10):
        self.label = tk.Label(frame, text=text_left,
                              background=BACKGROUND_COLOR)
        self.label.grid(row=rw, column=cl, sticky="w")
        self.text_variable = tk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)

        vcmd_int = (parent.register(validate_int),
                    '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR,
                              textvariable=self.text_variable, validate='key', validatecommand=vcmd_int)
        self.entry.config(width=width_specify)
        self.entry.grid(row=rw, column=cl+1, sticky="we", padx=pdx)

    def get_value(self):
        return int("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(int(value)))

    def disable(self):
        self.entry.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.entry.config(state="normal")
        self.label.config(state="normal")