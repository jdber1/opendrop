import tkinter as tk
from customtkinter import *
from utils.config import *
from utils.validators import *

class FloatEntry():
    def __init__(self, parent, frame, text_left, callback, rw=0, label_width=None, width_specify=10, state_specify='normal'):
        # Create a CTkLabel for the text on the left
        self.label = CTkLabel(frame, text=text_left, text_color="black")
        self.label.grid(row=rw, column=0, sticky="w")

        # Create a StringVar for the entry field
        self.text_variable = StringVar()

        # Add a trace callback for text_variable if a callback is provided
        if callback:
            self.text_variable.trace_add("write", callback)

        # Validation command for float entries (assuming validate_float is defined)
        vcmd_float = (parent.register(validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # Create the CTkEntry for float input
        self.entry = CTkEntry(frame, textvariable=self.text_variable, validate='key', validatecommand=vcmd_float)
        self.entry.configure(width=width_specify)

        # Position the entry field in the grid layout
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