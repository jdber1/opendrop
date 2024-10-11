import signal
import sys

from enum import Enum
from customtkinter import *
from .navigation import create_navigation  # Import the navigation bar
from .dynamic_content import DynamicContent
from .pd_acquisition import PdAcquisition
from .pd_preparation import PdPreparation
from .output_page import OutputPage

def call_user_input(user_input_data):
    PendantDropWindow(user_input_data)


class Stage(Enum):
    ACQUISITION = 1
    PREPARATION = 2
    # IMAGE_REGION = 3
    ANALYSIS = 3
    OUTPUT =4


class PendantDropWindow(CTk):
    def __init__(self, user_input_data):
        super().__init__()  # Call the parent class constructor
        self.title("Pendant Drop")
        self.geometry("1280x720")
        self.configure(fg_color="lightblue")
        self.widgets(user_input_data)

        self.stages = list(Stage)
        self.current_stage = Stage.ACQUISITION

        self.mainloop()  # Start the main loop
        
    def widgets(self, user_input_data):
        # Create the navigation bar (progress bar style)
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

        # Frames for each stage
        self.pd_acquisition_frame = PdAcquisition(self, user_input_data, fg_color="lightblue")
        self.pd_preparation_frame = PdPreparation(self, user_input_data, fg_color="lightblue")
        self.dynamic_frame = DynamicContent(self)
        self.output_frame = OutputPage(self, user_input_data, controller=self)  # Add the OutputPage frame

        self.pd_acquisition_frame.pack(fill="both", expand=True)
        
        # Frame for navigation buttons
        self.button_frame = CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", pady=10)

        # Add navigation buttons to the button frame
        self.back_button = CTkButton(self.button_frame, text="Back", command=self.back)
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(self.button_frame, text="Next", command=self.next)
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(self.button_frame, text="Save", command=self.save_output)
        self.save_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()  # Hide it initially

    def back(self):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) - 1) % len(self.stages)]
        # Go back to the previous screen
        if self.current_stage == Stage.ACQUISITION:
            self.pd_acquisition_frame.pack(fill="both", expand=True)
            self.pd_preparation_frame.pack_forget()
        elif self.current_stage == Stage.PREPARATION:
            self.pd_preparation_frame.pack(fill="both", expand=True)
            self.dynamic_frame.pack_forget()
        elif self.current_stage == Stage.ANALYSIS:
            self.dynamic_frame.pack(fill="both", expand=True)
            self.output_frame.pack_forget()

        # Show the next button and hide the save button when going back
        self.next_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()

    def next(self):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) + 1) % len(self.stages)]
        # Handle the "Next" button functionality
        if self.current_stage == Stage.PREPARATION:
            self.pd_acquisition_frame.pack_forget()
            self.pd_preparation_frame.pack(fill="both", expand=True)
        elif self.current_stage == Stage.ANALYSIS:
            self.pd_preparation_frame.pack_forget()
            self.dynamic_frame.pack(fill="both", expand=True)
        elif self.current_stage == Stage.OUTPUT:
            self.dynamic_frame.pack_forget()
            self.output_frame.pack(fill="both", expand=True)  # Show the OutputPage

            # Hide the next button and show the save button
            self.next_button.pack_forget()
            self.save_button.pack(side="right", padx=10, pady=10)

    def save_output(self):
        # Implement the save logic here
        print("Output saved!")
