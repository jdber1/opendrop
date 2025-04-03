import tkinter as tk

from utils.config import *
from utils.validators import *

class FloatEntry():
    def __init__(self, parent, frame, text_left, callback, rw=0, label_width=None, width_specify=10, state_specify='normal'):
        self.label = tk.Label(frame, text=text_left,
                              background=BACKGROUND_COLOR, width=label_width)
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)
            
        vcmd_float = (parent.register(validate_float),
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR,
                              textvariable=self.text_variable, validate='key', validatecommand=vcmd_float)
        self.entry.config(width=width_specify, state=state_specify)
        self.entry.grid(row=rw, column=1, sticky="we")

    def get_value(self):
        return float("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.entry.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.entry.config(state="normal")
        self.label.config(state="normal")