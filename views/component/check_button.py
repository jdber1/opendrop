from customtkinter import *


from utils.config import *

class CheckButton():
    def __init__(self, parent, frame, text_left, callback, rw=0, cl=0, width_specify=10, pdx=0, pdy=2, stcky="w", state_specify='normal'):  # , pd=5
        self._save_previous_variable = 0
        self.int_variable = IntVar()

        if callback:
            self.int_variable.trace_add("write", callback)

        # Replace tk.Checkbutton with CTkCheckBox
        self.check_button = CTkCheckBox(
            frame, text=text_left, variable=self.int_variable, state=state_specify)
        
        # Apply grid configuration
        self.check_button.grid(row=rw, column=cl, sticky=stcky, pady=pdy, padx=pdx)

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