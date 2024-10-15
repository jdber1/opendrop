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

from views.helper.validation import validate_user_input_data

def call_user_input(function_type, user_input_data, fitted_drop_data):
    FunctionWindow(function_type, user_input_data, fitted_drop_data)

class FunctionWindow(CTk):
    def __init__(self, function_type, user_input_data, fitted_drop_data):
        super().__init__()  # Call the parent class constructor
        self.FG_COLOR = "lightblue"
        self.title(function_type.value)
        self.geometry("1280x720")
        self.configure(fg_color=self.FG_COLOR)

        user_input_data.screen_resolution = [
            self.winfo_screenwidth(), self.winfo_screenheight()]
        
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
        self.navigation_frame = create_navigation(self)
        self.navigation_frame.pack(fill="x", pady=10)

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
                    self.ift_acquisition_frame.pack_forget()

                    # Initialise Preparation frame
                    self.ift_preparation_frame = IftPreparation(
                    self, user_input_data, fg_color=self.FG_COLOR)
                    self.ift_preparation_frame.pack(fill="both", expand=True)
                else:
                    self.ca_acquisition_frame.pack_forget()

                    # Initialise Preparation frame
                    self.ca_preparation_frame = CaPreparation(
                    self, user_input_data, fg_color=self.FG_COLOR)
                    self.ca_preparation_frame.pack(fill="both", expand=True) 
            else:
                self.update_stage(Move.Back.value)
                messagebox.showinfo("No Selection", "Please select at least one file.")
        
        elif self.current_stage == Stage.ANALYSIS:
            print("user_input_data.user_input_fields: ",user_input_data.user_input_fields)
            print("user_input_data.analysis_method_fields: ",user_input_data.analysis_method_fields)
            print("user_input_data.statistical_output: ",user_input_data.statistical_output)

            # Validate user input data
            validation_messages = validate_user_input_data(user_input_data)

            # TO DO: implement the validation when function type is contact angle
            if validation_messages and function_type == FunctionType.PENDANT_DROP:

                self.update_stage(Move.Back.value)
                all_messages = "\n".join(validation_messages)
                # Show a single pop-up message with all validation messages
                messagebox.showinfo("Missing: \n", all_messages)
            else:
                print("All required fields are filled.")

                if function_type == FunctionType.PENDANT_DROP:
                    self.ift_preparation_frame.pack_forget()
                    self.ift_analysis_frame = IftAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ift_analysis_frame.pack(fill="both", expand=True)
                else:
                    self.ca_preparation_frame.pack_forget()

                    CaDataProcessor.process_data(self, fitted_drop_data, user_input_data, None)

                    self.ca_analysis_frame = CaAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ca_analysis_frame.pack(fill="both", expand=True)

                # Initialise Analysis frame
                
        elif self.current_stage == Stage.OUTPUT:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_analysis_frame.pack(fill="both", expand=True)
            else:
                self.ca_analysis_frame.pack(fill="both", expand=True)

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