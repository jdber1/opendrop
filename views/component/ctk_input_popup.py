from customtkinter import CTkToplevel, CTkFrame, CTkLabel, CTkButton, CTkEntry, StringVar
from tkinter import messagebox

class CTkInputPopup(CTkToplevel):
    def __init__(self, parent, title="Input Required", prompt="Enter value:", on_confirm=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("300x200")
        self.resizable(False, False)

        self.prompt = prompt
        self.on_confirm = on_confirm if on_confirm is not None else self.default_confirm

        self.input_var = StringVar()

        # Create the popup frame
        self.popup_frame = CTkFrame(self)
        self.popup_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Create label for prompt text
        self.prompt_label = CTkLabel(self.popup_frame, text=self.prompt)
        self.prompt_label.pack(pady=(10, 5))

        # Create entry widget for input
        self.input_entry = CTkEntry(self.popup_frame, textvariable=self.input_var, width=200)
        self.input_entry.pack(pady=(5, 10))
        self.input_entry.focus()  # Focus the entry box

        # Create button for confirm action
        self.confirm_button = CTkButton(self.popup_frame, text="Confirm", command=self.on_confirm_wrapper)
        self.confirm_button.pack(pady=(10, 5))

    def on_confirm_wrapper(self):
        """Wrapper to pass the input value to the confirm function."""
        input_value = self.input_var.get()
        if input_value:
            self.on_confirm(input_value)
            self.destroy()
        else:
            messagebox.showwarning("Input Required", "Please enter a value.")

    def default_confirm(self, value):
        """Default confirmation function if none is provided."""
        print(f"Input value: {value}")
        messagebox.showinfo("Input Received", f"Entered Value: {value}")