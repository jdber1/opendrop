from customtkinter import *
from .navigation import create_navigation  # Import the navigation bar
from .dynamic_content import DynamicContent  # Import the dynamic content

def call_user_input(user_input_data):
    PenDantDropWindow(user_input_data)

class PenDantDropWindow(CTk):
    def __init__(self, user_input_data):
        super().__init__()  # Call the parent class constructor
        self.title("CustomTkinter Dynamic Content Example")
        self.geometry("1920x1080")
        
        self.switch_to_progress(user_input_data)

        self.mainloop()  # Start the main loop
        
    def switch_to_progress(self, user_input_data):
        # Create the navigation bar (progress bar style)
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

        # Create a frame for the dynamic content
        self.dynamic_frame = DynamicContent(self)
        self.dynamic_frame.pack(fill="both", expand=True)

        # Add navigation buttons (optional for next/back)
        self.back_button = CTkButton(self, text="Back", command=self.back_to_initial)
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(self, text="Next", command=self.on_next)
        self.next_button.pack(side="right", padx=10, pady=10)

    def back_to_initial(self):
        # Go back to the initial screen
        self.navigation_frame.pack_forget()
        self.dynamic_frame.pack_forget()
        self.start_button.pack()

    def on_next(self):
        # Handle the "Next" button functionality (if needed)
        print("Next stage in progress")
