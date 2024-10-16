import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from utils.config import *
from utils.validators import *

class FloatCombobox():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, padx=(5, 5), pady=(5, 5), width_specify=150, label_width=150, state_specify='normal'):
        self.label = ctk.CTkLabel(frame, text=text_left, width=label_width, anchor="w")
        self.label.grid(row=rw, column=0, sticky="w", padx=padx, pady=pady)
        self.text_variable = ctk.StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)

        self.float_variable = 0.0
        
        self.combobox = ctk.CTkComboBox(
            frame, variable=self.text_variable, values=options_list)
        self.combobox.configure(width=width_specify, state=state_specify)
        self.combobox.grid(row=rw, column=1, sticky="we", padx=padx, pady=pady)

    def get_value(self):
        value = 0
        try:
            value = float("0" + self.text_variable.get())
            self.float_variable = value
            return value
        except ValueError:
            # if the user enters non-numeric character
            self.set_value(self.float_variable)
            return self.float_variable

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.combobox.configure(state="disabled")
        self.label.configure(state="disabled")

    def normal(self):
        self.combobox.configure(state="normal")
        self.label.configure(state="normal")