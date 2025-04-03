import tkinter as tk
from tkinter import ttk

from utils.config import *
from utils.validators import *

class FloatCombobox():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, width_specify=10, label_width=None, state_specify='normal'):
        self.label = tk.Label(frame, text=text_left,
                              background=BACKGROUND_COLOR, width=label_width)
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)

        vcmd_float = (parent.register(validate_float),
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.combobox = ttk.Combobox(
            frame, textvariable=self.text_variable, validate='key', validatecommand=vcmd_float)
        self.combobox['values'] = options_list
        self.combobox.config(width=width_specify, state=state_specify)
        self.combobox.grid(row=rw, column=1, sticky="we")

    def get_value(self):
        return float("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.combobox.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.combobox.config(state="normal")
        self.label.config(state="normal")