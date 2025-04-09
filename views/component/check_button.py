import tkinter as tk
import customtkinter as ctk

from utils.config import *

class CheckButton():
    def __init__(self, parent, frame, text_left, callback, rw=0, cl=0, width_specify=10, padx=(5, 5), pady=(1, 1), stcky="w", state_specify='normal',initial_value=False):  # , pd=5
        self._save_previous_variable = 0
        self.int_variable = ctk.IntVar(value=int(initial_value))

        if callback:
            self.int_variable.trace_add("write", callback)

        self.check_button = ctk.CTkCheckBox(
            frame, text=text_left, variable=self.int_variable, state=state_specify, 
            border_width=2, checkbox_width=15, checkbox_height=15, corner_radius=5)
        # "CENTER") # sticky="w" padx=pd,
        self.check_button.grid(
            row=rw, column=cl, sticky=stcky, pady=pady, padx=padx)

    def get_value(self):
        return self.int_variable.get()

    def set_value(self, value):
        self.int_variable.set(value)

    def disable(self):
        self._save_previous_variable = self.get_value()
        self.set_value(0)
        self.check_button.configure(state="disabled")

    def normal(self):
        self.set_value(self._save_previous_variable)
        self.check_button.configure(state="normal")

    def state(self):
        return self.check_button.configure()['state'][-1]

    def grid_forget(self):
        self.check_button.grid_forget()