from customtkinter import *

from utils.config import *
from utils.validators import *

class FloatCombobox():
    def __init__(self, parent, frame, text_left, options_list, callback, rw=0, width_specify=10, label_width=None, state_specify='normal'):

        # Replace tk.Label with CTkLabel
        self.label = CTkLabel(frame, text=text_left, text_color="black")
        self.label.grid(row=rw, column=0, sticky="w")

        self.text_variable = StringVar()

        if callback:
            self.text_variable.trace_add("write", callback)

        # Validate float input, if needed (though Combobox usually does not validate text in real-time)
        vcmd_float = (parent.register(validate_float),
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # Replace ttk.Combobox with CTkComboBox
        self.combobox = CTkComboBox(frame, values=options_list, variable=self.text_variable)
        self.combobox.configure(width=width_specify, state=state_specify)
        self.combobox.grid(row=rw, column=1, sticky="we")
        # Bind the combobox selection event
        self.combobox.bind("<<ComboboxSelected>>", self.validate_float_input)

    def validate_float_input(self, event=None):
        """Custom method to validate float input after selection."""
        try:
            value = float(self.text_variable.get())
            # Optionally, you can do something with the valid value
            print(f"Valid float input: {value}")
        except ValueError:
            # Handle the invalid input case (e.g., show a message)
            print("Invalid input! Please enter a valid float.")

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