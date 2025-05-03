from customtkinter import *
from tkinter import messagebox

from modules.contact_angle.ca_data_processor import CaDataProcessor
from modules.ift.pd_data_processor import pdDataProcessor
from modules.core.classes import ExperimentalSetup, ExperimentalDrop #, DropData, Tolerances

from views.helper.theme import LIGHT_MODE
from views.helper.validation import validate_user_input_data_ift,validate_user_input_data_cm,validate_frame_interval

from views.helper.style import get_color
from views.navigation import create_navigation

from views.ift_acquisition import IftAcquisition
from views.ift_preparation import IftPreparation
from views.ift_analysis import IftAnalysis

from views.ca_acquisition import CaAcquisition
from views.ca_preparation import CaPreparation
from views.ca_analysis import CaAnalysis
from views.output_page import OutputPage

from utils.enums import *


def call_user_input(function_type, fitted_drop_data):
    FunctionWindow(function_type, fitted_drop_data)

class FunctionWindow(CTk):
    def __init__(self, function_type, fitted_drop_data):
        super().__init__()  # Call the parent class constructor
        self.title(function_type.value)
        self.geometry("1000x750")
        self.minsize(1000, 750) 

        if get_appearance_mode() == LIGHT_MODE:
            self.FG_COLOR = get_color("background")
        else:
            self.FG_COLOR = self.cget("fg_color")

        self.configure(fg_color=self.FG_COLOR)

        self.ca_processor = CaDataProcessor()
        self.pd_processor = pdDataProcessor()

        user_input_data = ExperimentalSetup()
        experimental_drop = ExperimentalDrop()

        user_input_data.screen_resolution = [
            self.winfo_screenwidth(), self.winfo_screenheight()]
        # temp
        user_input_data.save_images_boole = False
        user_input_data.create_folder_boole = False
        
        self.widgets(function_type, user_input_data,experimental_drop,fitted_drop_data)

        self.stages = list(Stage)
        self.current_stage = Stage.ACQUISITION

        self.mainloop()  # Start the main loop

    def widgets(self, function_type, user_input_data,experimental_drop,fitted_drop_data):
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
            self.button_frame, text="Next", command=lambda: self.next(function_type, user_input_data, experimental_drop,fitted_drop_data))
        self.next_button.pack(side="right", padx=10, pady=10)

        # Add save button for OutputPage (initially hidden)
        self.save_button = CTkButton(
            self.button_frame, text="Save", command=lambda: self.save_output(function_type, user_input_data))

    def back(self, function_type, user_input_data):
        self.update_stage(Move.Back.value)
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

    def next(self, function_type, user_input_data, experimental_drop, fitted_drop_data):
        self.update_stage(Move.Next.value)
        # Handle the "Next" button functionality
        if self.current_stage == Stage.PREPARATION:

            # First check if the user has imported files
            if not self.check_import(user_input_data):
                self.update_stage(Move.Back.value)
                messagebox.showinfo("No Selection", "Please select at least one file.")
                return

            # Then check if the frame interval is valid
            # if function_type == FunctionType.PENDANT_DROP:
            if not validate_frame_interval(user_input_data):
                self.update_stage(Move.Back.value)
                messagebox.showinfo("Missing", "Frame Interval is required.")
                return
            self.back_button.pack(side="left", padx=10, pady=10)

            # user have selected at least one file
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_acquisition_frame.pack_forget()

                # Initialise Preparation frame
                self.ift_preparation_frame = IftPreparation(
                self, user_input_data, experimental_drop,fg_color=self.FG_COLOR)
                self.ift_preparation_frame.pack(fill="both", expand=True)
            else:
                self.ca_acquisition_frame.pack_forget()

                # Initialise Preparation frame
                self.ca_preparation_frame = CaPreparation(
                self, user_input_data, experimental_drop,fg_color=self.FG_COLOR)
                self.ca_preparation_frame.pack(fill="both", expand=True) 


        elif self.current_stage == Stage.ANALYSIS:
            # Validate user input data
            if function_type == FunctionType.PENDANT_DROP:
                validation_messages = validate_user_input_data_ift(user_input_data)
            elif function_type == FunctionType.CONTACT_ANGLE:
                validation_messages = validate_user_input_data_cm(user_input_data,experimental_drop)
            
            if validation_messages:
                self.update_stage(Move.Back.value)
                all_messages = "\n".join(validation_messages)
                # Show a single pop-up message with all validation messages
                messagebox.showinfo("Missing: \n", all_messages)
            else:
                if function_type == FunctionType.PENDANT_DROP:
                    self.ift_preparation_frame.pack_forget()
                    self.ift_analysis_frame = IftAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ift_analysis_frame.pack(fill="both", expand=True)
                    print("FunctionType.PENDANT_DROP")
                  
                else:
                    self.ca_preparation_frame.pack_forget()
                    self.ca_analysis_frame = CaAnalysis(
                        self, user_input_data, fg_color=self.FG_COLOR)
                    self.ca_analysis_frame.pack(fill="both", expand=True)
                    
                    print("FunctionType.Contact_Angle")
                    # analysis the given input data and send the output to the ca_analysis_frame for display
                    self.withdraw()
                    self.ca_processor.process_data(fitted_drop_data, user_input_data, callback=self.ca_analysis_frame.receive_output)
                    self.deiconify()

        elif self.current_stage == Stage.OUTPUT:
            if function_type == FunctionType.PENDANT_DROP:
                self.ift_analysis_frame.pack_forget()
            else:
                self.ca_analysis_frame.pack_forget()

            # Initialise Output frame
            self.output_frame = OutputPage(self, user_input_data)
            # Show the OutputPage
            self.output_frame.pack(fill="both", expand=True)

            # Hide the next button and show the save button
            self.next_button.pack_forget()
            self.save_button.pack(side="right", padx=10, pady=10)

    def save_output(self, function_type, user_input_data):
        if function_type == FunctionType.PENDANT_DROP:
            messagebox.showinfo("Messagebox", "TODO: save file")
            self.destroy()
        else:
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
        if direction == Move.Next.value:
            self.next_stage()
        elif direction == Move.Back.value:
            self.prev_stage()

    def check_import(self, user_input_data):
        return user_input_data.number_of_frames is not None and user_input_data.number_of_frames > 0 and user_input_data.import_files is not None and len(user_input_data.import_files) > 0 and len(user_input_data.import_files) == user_input_data.number_of_frames

    def on_closing(self):
        """处理窗口关闭事件"""
        try:
            # 取消所有待处理的定时器事件
            for after_id in self.tk.call('after', 'info'):
                try:
                    self.after_cancel(after_id)
                except:
                    pass
            
            # 清理所有子部件
            for widget in self.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
                    
            # 停止主循环
            self.quit()
            
            # 销毁窗口
            self.destroy()
        except:
            # 如果出现任何错误，强制退出
            import sys
            sys.exit(0)