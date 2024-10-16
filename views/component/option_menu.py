from customtkinter import *
from utils.config import *

class OptionMenu():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, default_value=None,width_specify=15, label_width=None):
        self.entry_list = options_list
        # Use CTkLabel instead of tk.Label
        self.label = CTkLabel(
            frame, text=text_left, anchor="w")
        self.label.grid(row=rw, column=0, sticky="w")
        
        # Initialize StringVar and set default value if provided
        self.text_variable = StringVar(value=default_value if default_value in options_list else options_list[0])

        if callback:
            self.text_variable.trace_add("write", callback)

        # Use CTkOptionMenu instead of tk.OptionMenu
        self.optionmenu = CTkOptionMenu(
            frame, variable=self.text_variable, values=self.entry_list)
        
        self.optionmenu.configure(width=width_specify)
        self.optionmenu.grid(row=rw, column=1, sticky="w")

    def get_value(self):
        return self.text_variable.get()

    def set_value(self, value):
        if value in self.entry_list:
            self.text_variable.set(value)
        else:
            self.text_variable.set(self.entry_list[0])  # Set to first option if value not found

    def disable(self):
        self.optionmenu.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.optionmenu.config(state="normal")
        self.label.config(state="normal")
