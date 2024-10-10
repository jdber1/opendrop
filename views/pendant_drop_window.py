from enum import Enum

from customtkinter import *
from .navigation import create_navigation  # Import the navigation bar
from .dynamic_content import DynamicContent
from .pd_acquisition import PdAcquisition
from .pd_preparation import PdPreparation

def call_user_input(user_input_data):
    PenDantDropWindow(user_input_data)

class Stage(Enum):
    ACQUISITION = 1
    PREPARATION = 2
    ANALYSIS = 3
    OUTPUT = 4

class PenDantDropWindow(CTk):
    def __init__(self, user_input_data):
        super().__init__()  # Call the parent class constructor
        self.title("CustomTkinter Dynamic Content Example")
        self.geometry("1920x1080")
        
        self.widgets(user_input_data)

        self.stages = list(Stage)

        self.current_stage = Stage.ACQUISITION

        self.mainloop()  # Start the main loop
        
    def widgets(self, user_input_data):
        # Create the navigation bar (progress bar style)
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

        self.pd_acquisition_frame = PdAcquisition(self)
        self.dynamic_content = DynamicContent(self)
        self.pd_preparation_frame = PdPreparation(self)

        self.pd_acquisition_frame.pack(fill="both", expand=True)

        # Add navigation buttons (optional for next/back)
        self.back_button = CTkButton(self, text="Back", command=self.back)
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(self, text="Next", command=self.next)
        self.next_button.pack(side="right", padx=10, pady=10)

    def back(self):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) - 1) % len(self.stages)]
        # Go back to the initial screen
        if (self.current_stage == Stage.ACQUISITION):
            self.pd_acquisition_frame.pack(fill="both", expand=True)
            self.pd_preparation_frame.pack_forget()
        elif (self.current_stage == Stage.PREPARATION):
            self.pd_preparation_frame.pack()
            self.dynamic_frame.pack_forget()
        elif (self.current_stage == Stage.ANALYSIS):
        
            self.dynamic_frame.pack()
            self.dynamic_frame.pack_forget()
        elif (self.current_stage == Stage.OUTPUT):
            self.destroy()


    def next(self):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) + 1) % len(self.stages)]
        # Handle the "Next" button functionality
        if (self.current_stage == Stage.PREPARATION):
            self.pd_acquisition_frame.pack_forget()
            self.pd_preparation_frame.pack()
        elif (self.current_stage == Stage.ANALYSIS):
            self.pd_preparation_frame.pack_forget()
            self.dynamic_frame.pack()
        elif (self.current_stage == Stage.OUTPUT):
            self.dynamic_frame.pack_forget()
            self.dynamic_frame.pack()
