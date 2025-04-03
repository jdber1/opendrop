import tkinter as tk

from utils.config import *

class CheckButton():
    def __init__(self, parent, frame, text_left, callback, rw=0, cl=0, width_specify=10, pdx=0, pdy=2, stcky="w", state_specify='normal'):  # , pd=5
        self._save_previous_variable = 0
        self.int_variable = tk.IntVar()

        if callback:
            self.int_variable.trace_add("write", callback)

        self.check_button = tk.Checkbutton(
            frame, text=text_left, background=BACKGROUND_COLOR, variable=self.int_variable, state=state_specify)
        # "CENTER") # sticky="w" padx=pd,
        self.check_button.grid(
            row=rw, column=cl, sticky=stcky, pady=pdy, padx=pdx)

    def get_value(self):
        return self.int_variable.get()

    def set_value(self, value):
        self.int_variable.set(value)

    def disable(self):
        self._save_previous_variable = self.get_value()
        self.set_value(0)
        self.check_button.config(state="disabled")

    def normal(self):
        self.set_value(self._save_previous_variable)
        self.check_button.config(state="normal")

    def state(self):
        return self.check_button.config()['state'][-1]

    def grid_forget(self):
        self.check_button.grid_forget()