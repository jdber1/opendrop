import tkinter as tk
import customtkinter as ctk

from utils.config import *
from utils.validators import *

class FloatEntry():
    def __init__(self, parent, frame, text_left, callback, rw=0, padx=(5, 5), pady=(5, 5), width_specify=150, label_width=150, state_specify='normal'):
        self.label = ctk.CTkLabel(frame, text=text_left, width=label_width)
        self.label.grid(row=rw, column=0, sticky="w", padx=padx, pady=pady)
        self.text_variable = ctk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)
            
        vcmd_float = (parent.register(validate_float),
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = ctk.CTkEntry(frame,
                              textvariable=self.text_variable, validate='key', validatecommand=vcmd_float)
        self.entry.configure(width=width_specify, state=state_specify)
        self.entry.grid(row=rw, column=1, sticky="we", padx=padx, pady=pady)

    def get_value(self):
        return float("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.entry.configure(state="disabled")
        self.label.configure(state="disabled")

    def normal(self):
        self.entry.configure(state="normal")
        self.label.configure(state="normal")