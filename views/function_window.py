from customtkinter import *
from tkinter import messagebox

from .navigation import create_navigation

from .ift_acquisition import IftAcquisition
from .ift_preparation import IftPreparation
from .ift_analysis import IftAnalysis

from .ca_acquisition import CaAcquisition
from .ca_preparation import CaPreparation
from .ca_analysis import CaAnalysis

from .output_page import OutputPage

from modules.ca_data_processor import CaDataProcessor
from utils.enums import *

from views.helper.theme import get_system_appearance, DARK_MODE, LIGHT_MODE
from views.helper.validation import validate_user_input_data_ift,validate_user_input_data_cm

def call_user_input(function_type, user_input_data, fitted_drop_data):
    FunctionWindow(function_type, user_input_data, fitted_drop_data)

class FunctionWindow(CTk):
    def __init__(self, function_type, user_input_data, fitted_drop_data):
        super().__init__()  # Call the parent class constructor
        self.title(function_type.value)
        self.geometry("1080x720")

        if get_appearance_mode() == LIGHT_MODE:
            self.FG_COLOR = "lightblue"
        else:
            self.FG_COLOR = self.cget("fg_color")

        self.configure(fg_color=self.FG_COLOR)

        user_input_data.screen_resolution = [
            self.winfo_screenwidth(), self.winfo_screenheight()]
        # temp
        user_input_data.save_images_boole = False
        user_input_data.create_folder_boole = False
        
        self.widgets(function_type, user_input_data, fitted_drop_data)

        self.stages = list(Stage)
        self.current_stage = Stage.ACQUISITION

        def on_exit():
            sys.exit(0)

        # Bind the window close button (X) to the on_exit function
        self.protocol("WM_DELETE_WINDOW", on_exit)

        self.mainloop()  # Start the main loop

    def widgets(self, function_type, user_input_data, fitted_drop_data):
        # Create the navigation bar (progress bar style)
        self.next_stage, self.prev_stage = create_navigation(self)
        

        # Initialise frame for first stage
        self.ift_acquisition_frame = IftAcquisition(
                self, user_input_data, fg_color=self.FG_COLOR)
        self.ca_acquisition_frame = CaAcquisition(
                self, user_input_data, fg_color=self.FG_COLOR)
        
        if function_type == FunctionType.PENDANT_DROP:
            self.ift_acquisition_frame.pack(fill="both", expand=True)
        elif function_type == FunctionType.CONTACT_ANGLE:
            self.ca_acquisition_frame.pack(fill="both", expand=True)

        # Frame for navigation buttons
        self.button_frame = CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", pady=10)

        # Add navigation buttons to the button frame
        self.back_button = CTkButton(
            self.button_frame, text="Back", command=lambda: self.back(function_type, user_input_data))
        self.back_button.pack(side="left", padx=10, pady=10)

        self.next_button = CTkButton(
            self.button_frame, text="Next", command=lambda: self.next(function_type, user_input_data, fitted_drop_data))
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(
            self.button_frame, text="Save", command=self.save_output)

    def back(self, function_type, user_input_data):
        self.update_stage(Move.Back.value)
        self.prev_stage()
        # Go back to the previous screen
        if self.current_stage == Stage.ACQUISITION:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_acquisition_frame.pack(fill="both", expand=True)
                self.ift_preparation_frame.pack_forget()
            else:
                self.ca_acquisition_frame.pack(fill="both", expand=True)
                self.ca_preparation_frame.pack_forget()

        elif self.current_stage == Stage.PREPARATION:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_preparation_frame.pack(fill="both", expand=True)
            else:
                self.ca_preparation_frame.pack(fill="both", expand=True)

            self.ift_analysis_frame.pack_forget()

        elif self.current_stage == Stage.ANALYSIS:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_analysis_frame.pack(fill="both", expand=True)
            else:
                self.ca_analysis_frame.pack(fill="both", expand=True)
            
            self.output_frame.pack_forget()

        # Show the next button and hide the save button when going back
        self.next_button.pack(side="right", padx=10, pady=10)
        self.save_button.pack_forget()

    def next(self, function_type, user_input_data, fitted_drop_data):
        self.update_stage(Move.Next.value)
        # Handle the "Next" button functionality
        if self.current_stage == Stage.PREPARATION:
            if self.check_import(user_input_data):
                # user have selected at least one file
                if function_type == FunctionType.PENDANT_DROP:
                    self.next_stage()
                    self.ift_acquisition_frame.pack_forget()

                    # Initialise Preparation frame
                    self.ift_preparation_frame = IftPreparation(
                    self, user_input_data, fg_color=self.FG_COLOR)
                    self.ift_preparation_frame.pack(fill="both", expand=True)
                else:
                    self.next_stage()
                    self.ca_acquisition_frame.pack_forget()

                    # Initialise Preparation frame
                    self.ca_preparation_frame = CaPreparation(
                    self, user_input_data, fg_color=self.FG_COLOR)
                    self.ca_preparation_frame.pack(fill="both", expand=True) 
            else:
                self.update_stage(Move.Back.value)
                messagebox.showinfo("No Selection", "Please select at least one file.")
        
        elif self.current_stage == Stage.ANALYSIS:

            # Validate user input data
            if function_type == FunctionType.PENDANT_DROP:
                validation_messages = validate_user_input_data_ift(user_input_data)
            elif function_type == FunctionType.CONTACT_ANGLE:
                validation_messages = validate_user_input_data_cm(user_input_data)
            

            # TO DO: implement the validation when function type is contact angle
            if validation_messages:

                self.update_stage(Move.Back.value)
                all_messages = "\n".join(validation_messages)
                # Show a single pop-up message with all validation messages
                messagebox.showinfo("Missing: \n", all_messages)
            else:
                print("All required fields are filled.")
                self.next_stage()
                if function_type == FunctionType.PENDANT_DROP:
                    self.ift_preparation_frame.pack_forget()
                    self.ift_analysis_frame = IftAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ift_analysis_frame.pack(fill="both", expand=True)
                else:
                    self.ca_preparation_frame.pack_forget()
                    self.ca_analysis_frame = CaAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ca_analysis_frame.pack(fill="both", expand=True)

                    processor = CaDataProcessor()
                    processor.process_data(fitted_drop_data, user_input_data, callback=self.ca_analysis_frame.receive_output)

                # Initialise Analysis frame
                
        elif self.current_stage == Stage.OUTPUT:
            self.next_stage()
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_analysis_frame.pack_forget()
            else:
                self.ca_analysis_frame.pack_forget()

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
    
    def update_stage(self, direction):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) + direction) % len(self.stages)]

    def check_import(self, user_input_data):
        return user_input_data.number_of_frames is not None and user_input_data.number_of_frames > 0 and user_input_data.import_files is not None and len(user_input_data.import_files) > 0 and len(user_input_data.import_files) == user_input_data.number_of_frames