from customtkinter import CTk, CTkFrame, CTkButton

class DynamicContent(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color=parent.cget("bg"))

        # Initially display the input fields
        self.run_input_fields()

    def run_input_fields(self):
        """Run the input fields setup using the InputFields class."""
        from .input_fields import InputFields  # Local import to avoid circular dependencies
        print("Setting up input fields...")
        
        # Store the input fields in an instance variable
        self.input_fields = InputFields(self)  # Instantiate the InputFields class
        self.input_fields.pack(fill="both", expand=True)  # Display the input fields
        
        # Add navigation buttons (optional for next/back)
        self.back_button = CTkButton(self, text="Back", command=self.back_to_initial)
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(self, text="Next", command=self.switch_to_image_app)
        self.next_button.pack(side="right", padx=10, pady=10)

    def switch_to_image_app(self):
        from .image_processing import ImageApp
        """Replace the current content with ImageApp."""
        
        # Remove input fields and the buttons
        self.input_fields.pack_forget()  # Hide input fields
        self.back_button.pack_forget()  # Hide the back button
        self.next_button.pack_forget()  # Hide the next button

        # Add the ImageApp into the same frame
        self.image_app = ImageApp(self)  # Pass the same parent (self)
        self.image_app.pack(fill="both", expand=True)
        
    def back_to_initial(self):
        # Go back to the initial screen (you need to define how the initial screen looks)
        print("Going back to initial screen...")
        # Here, you'd define what happens when "Back" is pressed

# Example usage
if __name__ == "__main__":
    root = CTk()  # Create the main application window (CTk instance)
    root.geometry("800x600")  # Optional: Set window size

    # Create an instance of the DynamicContent frame, which includes the input fields and button
    dynamic_content = DynamicContent(root)
    dynamic_content.pack(fill="both", expand=True)  # Make the frame expand and fill the window

    root.mainloop()  # Start the main event loop
