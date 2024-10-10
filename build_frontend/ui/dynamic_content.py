# dynamic_content.py

from customtkinter import CTk, CTkFrame
from .input_fields import InputFields  # Use an absolute import
 # Import the InputFields class
# from .dynamic_content import DynamicContent

class DynamicContent(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color=parent.cget("bg"))

    def run_input_fields(self):
        """Run the input fields setup using the InputFields class."""
        print("heelo")
        InputFields(self)  # Instantiate the InputFields class and pass the frame as parent


# Example usage
if __name__ == "__main__":
    root = CTk()  # Create a CTk instance
    dynamic_content = DynamicContent(root)  # Create the DynamicContent instance
    dynamic_content.pack(fill="both", expand=True)  # Pack the dynamic content frame

    # Run the single command to set up input fields
    dynamic_content.run_input_fields()

    root.mainloop()  # Start the main loop
