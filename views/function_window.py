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
from modules.ExtractData import ExtractedData

from views.helper.theme import LIGHT_MODE

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

        self.ca_processor = CaDataProcessor()

        user_input_data.screen_resolution = [
            self.winfo_screenwidth(), self.winfo_screenheight()]
        # temp
        user_input_data.save_images_boole = False
        user_input_data.create_folder_boole = False
        
        self.widgets(function_type, user_input_data, fitted_drop_data)

        self.stages = list(Stage)
        self.current_stage = Stage.ACQUISITION

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

        self.next_button = CTkButton(
            self.button_frame, text="Next", command=lambda: self.next(function_type, user_input_data, fitted_drop_data))
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(
            self.button_frame, text="Save", command=lambda: self.save_output(user_input_data))

    def back(self, function_type, user_input_data):
        self.update_stage(Move.Back.value)
        self.prev_stage()
        # Go back to the previous screen
        if self.current_stage == Stage.ACQUISITION:
            self.back_button.pack_forget()
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_acquisition_frame.pack(fill="both", expand=True)
                self.ift_preparation_frame.pack_forget()
            else:
                self.ca_acquisition_frame.pack(fill="both", expand=True)
                self.ca_preparation_frame.pack_forget()

        elif self.current_stage == Stage.PREPARATION:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_preparation_frame.pack(fill="both", expand=True)
                self.ift_analysis_frame.pack_forget()
            else:
                self.ca_preparation_frame.pack(fill="both", expand=True)
                self.ca_analysis_frame.pack_forget()

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

                self.back_button.pack(side="left", padx=10, pady=10)
                self.next_stage()

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
            # Validate user input data
            if function_type == FunctionType.PENDANT_DROP:
                validation_messages = validate_user_input_data_ift(user_input_data)
            elif function_type == FunctionType.CONTACT_ANGLE:
                validation_messages = validate_user_input_data_cm(user_input_data)
            
            if validation_messages:

                self.update_stage(Move.Back.value)
                all_messages = "\n".join(validation_messages)
                # Show a single pop-up message with all validation messages
                messagebox.showinfo("Missing: \n", all_messages)
            else:
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

                    self.ca_processor.process_data(fitted_drop_data, user_input_data, callback=self.ca_analysis_frame.receive_output)

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

    def save_output(self, user_input_data):
        # filename = user_input_data.filename[:-4] + '_' + user_input_data.time_string + ".csv"
        if user_input_data.filename:
            filename = user_input_data.filename + '_' + user_input_data.time_string + ".csv"
        else:
            filename = "Extracted_data" + '_' + user_input_data.time_string + ".csv"
        # export_filename = os.path.join(user_input_data.directory_string, filename)
        self.ca_processor.save_result(user_input_data.import_files, user_input_data.output_directory, filename)

        messagebox.showinfo("Success", "File saved successfully!")
        self.destroy()
    
    def update_stage(self, direction):
        self.current_stage = self.stages[(self.stages.index(self.current_stage) + direction) % len(self.stages)]

    def check_import(self, user_input_data):
        return user_input_data.number_of_frames is not None and user_input_data.number_of_frames > 0 and user_input_data.import_files is not None and len(user_input_data.import_files) > 0 and len(user_input_data.import_files) == user_input_data.number_of_frames