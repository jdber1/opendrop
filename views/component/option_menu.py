import tkinter as tk
import customtkinter as ctk

from utils.config import *

class OptionMenu():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, padx=(5, 5), pady=(5, 5), default_value=None, width_specify=150, label_width=150):
        self.entry_list = options_list
        self.label = ctk.CTkLabel(
            frame, text=text_left, width=label_width, anchor="w")
        self.label.grid(row=rw, column=0, sticky="w", padx=padx, pady=pady)
        
        # Initialize StringVar and set default value if provided
        self.text_variable = ctk.StringVar(value=default_value if default_value in options_list else options_list[0])
        
        self.optionmenu = ctk.CTkOptionMenu(frame, 
                                        variable=self.text_variable, 
                                        values=options_list,
                                        width=width_specify,
                                        command=callback)
        
        self.optionmenu.grid(row=rw, column=1, sticky="w", padx=padx, pady=pady)

    def get_value(self):
        return self.text_variable.get()

    def set_value(self, value):
        if value in self.entry_list:
            self.text_variable.set(value)
        else:
            self.text_variable.set(self.entry_list[0])  # Set to first option if value not found

    def disable(self):
        self.optionmenu.configure(state="disabled")
        self.label.configure(state="disabled")

    def normal(self):
        self.optionmenu.configure(state="normal")
        self.label.configure(state="normal")
