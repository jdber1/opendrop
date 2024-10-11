from enum import Enum
from customtkinter import *
from tkinter import messagebox

from .navigation import create_navigation
from .dynamic_content import DynamicContent
from .pd_acquisition import PdAcquisition
from .pd_preparation import PdPreparation
from .output_page import OutputPage

class Stage(Enum):
    ACQUISITION = 1
    PREPARATION = 2
    # IMAGE_REGION = 3
    ANALYSIS = 3
    OUTPUT = 4

class Move(Enum):
    Next = 1
    Back = -1

def call_user_input(user_input_data):
    PendantDropWindow(user_input_data)

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
        self.pd_acquisition_frame.pack(fill="both", expand=True)
        
        # Frame for navigation buttons
        self.button_frame = CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", pady=10)

        # Add navigation buttons to the button frame
        self.back_button = CTkButton(self.button_frame, text="Back", command=lambda: self.back(user_input_data))
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(self.button_frame, text="Next", command=lambda: self.next(user_input_data))
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(self.button_frame, text="Save", command=self.save_output)
        self.save_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()  # Hide it initially

    def validate_user_input_data(self,user_input_data):
        """Validate the user input data and return messages for missing fields."""
        messages = []

        user_input_fields = user_input_data.user_input_fields
            # Ensure if drop region is chosen, it must not be None
        if user_input_fields['drop_region_choice'] != 'Automated' and user_input_data.ift_drop_region is None:
            messages.append("Please select drop region")

        # Ensure if needle region is chosen, it must not be None
        if user_input_fields['needle_region_choice'] != 'Automated' and user_input_data.ift_needle_region is None:
            messages.append("Please select needle region")

            # Check user_input_fields for None values
        
        required_fields = {
            'drop_region_choice': "Drop Region Choice",
            'needle_region_choice': "Needle Region Choice",
            'drop_density': "Drop Density",
            'needle_diameter': "Needle Diameter",
            'continuous_density': "Continuous Density",
            'pixel_mm': "Pixel to mm"
        }

        for field, label in required_fields.items():
            if user_input_fields.get(field) is None:
                messages.append(f"{label} is required")

        # Check if analysis_method_fields has at least one method selected
        analysis_method_fields = user_input_data.analysis_method_fields
        if not any(analysis_method_fields.values()):
            messages.append("At least one analysis method must be selected.")

        return messages
    def back(self, user_input_data):
        self.update_stage(Move.Back.value)
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

    def next(self, user_input_data):
        self.update_stage(Move.Next.value)
        # Handle the "Next" button functionality
        if self.current_stage == Stage.PREPARATION:
            if self.check_import(user_input_data):
                # user have selected at least one file
                self.pd_acquisition_frame.pack_forget()
                # Note: Need to initialize there so that the frame can get the updated user_input_data
                self.pd_preparation_frame = PdPreparation(self, user_input_data, fg_color="lightblue")
                self.pd_preparation_frame.pack(fill="both", expand=True)
            else:
                self.update_stage(Move.Back.value)
                messagebox.showinfo("No Selection", "Please select at least one file.")
        
        elif self.current_stage == Stage.ANALYSIS:
            print("user_input_data.user_input_fields: ",user_input_data.user_input_fields)
            print("user_input_data.analysis_method_fields: ",user_input_data.analysis_method_fields)
            print("user_input_data.statistical_output: ",user_input_data.statistical_output)
            # Validate user input data
            validation_messages = self.validate_user_input_data(user_input_data)

            if validation_messages:
                # Print out the messages
                self.update_stage(Move.Back.value)
                all_messages = "\n".join(validation_messages)
                # Show a single pop-up message with all validation messages
                messagebox.showinfo("Missing: \n", all_messages)
            else:
                print("All required fields are filled.")
                self.pd_preparation_frame.pack_forget()
                # Temp use. Replace it with the analysis frame
                self.dynamic_frame = DynamicContent(self)
                self.dynamic_frame.pack(fill="both", expand=True)
        elif self.current_stage == Stage.OUTPUT:
            self.dynamic_frame.pack_forget()
            # Note: Need to initialize there so that the frame can get the updated user_input_data
            self.output_frame = OutputPage(self, user_input_data, controller=self)
            self.output_frame.pack(fill="both", expand=True)  # Show the OutputPage

            # Hide the next button and show the save button
            self.next_button.pack_forget()
            self.save_button.pack(side="right", padx=10, pady=10)

    def save_output(self):
        # Implement the save logic here
        print("Output saved!")
    
    def update_stage(self, direction):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) + direction) % len(self.stages)]

    def check_import(self, user_input_data):
        return user_input_data.number_of_frames is not None and user_input_data.number_of_frames > 0 and user_input_data.import_files is not None and len(user_input_data.import_files) > 0 and len(user_input_data.import_files) == user_input_data.number_of_frames
