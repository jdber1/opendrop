from enum import Enum
from customtkinter import *
from tkinter import messagebox

from .navigation import create_navigation
from .pd_acquisition import PdAcquisition
from .pd_preparation import PdPreparation
from .ift_analysis import IftAnalysis
from .output_page import OutputPage


def call_user_input(user_input_data):
    PendantDropWindow(user_input_data)


class Stage(Enum):
    ACQUISITION = 1
    PREPARATION = 2
    # IMAGE_REGION = 3
    ANALYSIS = 3
    OUTPUT = 4


class PendantDropWindow(CTk):
    def __init__(self, user_input_data):
        super().__init__()  # Call the parent class constructor
        self.FG_COLOR = "lightblue"
        self.title("Pendant Drop")
        self.geometry("1280x720")
        self.configure(fg_color=self.FG_COLOR)
        self.widgets(user_input_data)

        self.stages = list(Stage)
        self.current_stage = Stage.ACQUISITION

        self.mainloop()  # Start the main loop

    def widgets(self, user_input_data):
        # Create the navigation bar (progress bar style)
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

        # Initialise frame for first stage
        self.pd_acquisition_frame = PdAcquisition(
            self, user_input_data, fg_color=self.FG_COLOR)
        self.pd_acquisition_frame.pack(fill="both", expand=True)

        # Frame for navigation buttons
        self.button_frame = CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", pady=10)

        # Add navigation buttons to the button frame
        self.back_button = CTkButton(
            self.button_frame, text="Back", command=lambda: self.back(user_input_data))
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(
            self.button_frame, text="Next", command=lambda: self.next(user_input_data))
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(
            self.button_frame, text="Save", command=self.save_output)
        self.save_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()  # Hide it initially

    def back(self, user_input_data):
        self.current_stage = self.stages[(self.stages.index(
            self.current_stage) - 1) % len(self.stages)]
        # Go back to the previous screen
        if self.current_stage == Stage.ACQUISITION:
            self.pd_acquisition_frame.pack(fill="both", expand=True)
            self.pd_preparation_frame.pack_forget()
        elif self.current_stage == Stage.PREPARATION:
            self.pd_preparation_frame.pack(fill="both", expand=True)
            self.pd_analysis_frame.pack_forget()
        elif self.current_stage == Stage.ANALYSIS:
            self.pd_analysis_frame.pack(fill="both", expand=True)
            self.output_frame.pack_forget()

        # Show the next button and hide the save button when going back
        self.next_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()

    def next(self, user_input_data):
        self.current_stage = self.stages[(self.stages.index(
            self.current_stage) + 1) % len(self.stages)]
        # Handle the "Next" button functionality
        if self.current_stage == Stage.PREPARATION:
            if (user_input_data.number_of_frames is not None and user_input_data.number_of_frames > 0):
                # user have selected at least one file
                self.pd_acquisition_frame.pack_forget()
                # Note: Need to initialize there so that the frame can get the updated user_input_data

                # Initialise Preparation frame
                self.pd_preparation_frame = PdPreparation(
                    self, user_input_data, fg_color=self.FG_COLOR)
                self.pd_preparation_frame.pack(fill="both", expand=True)
            else:
                messagebox.showinfo(
                    "No Selection", "Please select at least one file.")
        elif self.current_stage == Stage.ANALYSIS:
            self.pd_preparation_frame.pack_forget()

            # Initialise Analysis frame
            self.pd_analysis_frame = IftAnalysis(
                self, user_input_data, fg_color=self.FG_COLOR)
            self.pd_analysis_frame.pack(fill="both", expand=True)
        elif self.current_stage == Stage.OUTPUT:
            self.pd_analysis_frame.pack_forget()
            # Note: Need to initialize there so that the frame can get the updated user_input_data

            # Initialise Output frame
            self.output_frame = OutputPage(
                self, user_input_data, controller=self)
            # Show the OutputPage
            self.output_frame.pack(fill="both", expand=True)

            # Hide the next button and show the save button
            self.next_button.pack_forget()
            self.save_button.pack(side="right", padx=10, pady=10)

    def save_output(self):
        # Implement the save logic here
        print("Output saved!")
