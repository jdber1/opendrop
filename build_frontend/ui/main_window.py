from customtkinter import *
from .navigation import create_navigation  # Import the navigation bar
from .dynamic_content import DynamicContent  # Import the dynamic content


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.title("CustomTkinter Dynamic Content Example")
        self.geometry("1920x1080")

        # Create the initial screen with a "Start" button
        self.initial_frame = CTkFrame(self)
        self.initial_frame.pack(fill="both", expand=True)

        self.start_button = CTkButton(
            self.initial_frame, text="Start", command=self.switch_to_progress)
        self.start_button.pack(pady=100)  # Center the button

    def switch_to_progress(self):
        from .navigation import create_navigation
        # Clear the initial frame
        self.initial_frame.pack_forget()

        # Create the navigation bar (progress bar style)
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

        # Create a frame for the dynamic content
        self.dynamic_frame = DynamicContent(self)
        self.dynamic_frame.pack(fill="both", expand=True)

        # # Add navigation buttons (optional for next/back)
        # self.back_button = CTkButton(self, text="Back", command=self.back_to_initial)
        # self.back_button.pack(side="left", padx=10, pady=10)

        # self.next_button = CTkButton(self, text="Next", command=self.on_next)
        # self.next_button.pack(side="right", padx=10, pady=10)

    def back_to_initial(self):
        # Go back to the initial screen
        self.navigation_frame.pack_forget()
        self.dynamic_frame.pack_forget()
        self.start_button.pack()
        self.initial_frame.pack(fill="both", expand=True)

    def on_next(self):
        # Handle the "Next" button functionality (if needed)
        print("Next stage in progress")
