from customtkinter import *
import tkinter as tk
from tkinter import filedialog, messagebox

from utils.config import *
from utils.validators import *
from .component.option_menu import OptionMenu
from .component.integer_entry import IntegerEntry

class CaAcquisition(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)  
        self.user_input_data = user_input_data

        # temp
        self.user_input_data.save_images_boole = False
        self.user_input_data.create_folder_boole = False

        self.setup_image_source_frame()
        self.setup_choose_files_frame()

        self.frame_interval_frame = CTkFrame(self, fg_color="transparent")

        image_acquisition_frame = tk.LabelFrame(
            self, text="Image acquisition", height=15, padx=30, pady=10)
        image_acquisition_frame.config(background=BACKGROUND_COLOR)
        image_acquisition_frame.grid(
            row=5, columnspan=4, rowspan=1, sticky="we", padx=15, pady=10)

        image_acquisition_frame.grid_columnconfigure(2, weight=1)

        self.image_source = OptionMenu(self, image_acquisition_frame, "Image source:",
                                            IMAGE_SOURCE_OPTIONS, self.update_image_source, rw=0, label_width=12)  # (LABEL_WIDTH-ENTRY_WIDTH))

        self.edgefinder = OptionMenu(
            self, image_acquisition_frame, "Edge finder:", EDGEFINDER_OPTIONS, self.update_edgefinder, rw=1, label_width=12)  # added by DS 31/5/21

        self.number_frames = IntegerEntry(
            self, image_acquisition_frame, "Number of frames:", None, rw=3, cl=0, pdx=10)
        self.wait_time = IntegerEntry(
            self, image_acquisition_frame, "Wait time (s):", self.update_wait_time, rw=4, cl=0, pdx=10)

    def setup_image_source_frame(self):
        """Set up the image source frame and its components."""
        self.image_source_frame = CTkFrame(self, fg_color="transparent")
        self.image_source_frame.grid(pady=(20, 5))
        self.setup_component_label(self.image_source_frame, "Image Source: ")
        self.image_source = StringVar(value=IMAGE_SOURCE_OPTIONS[0])
        self.option_menu = CTkOptionMenu(self.image_source_frame, 
                                              variable=self.image_source, 
                                              values=IMAGE_SOURCE_OPTIONS,
                                              command=self.show_image_source_frame)
        self.option_menu.grid()

    def show_image_source_frame(self, selection):
        """Display the corresponding frame based on the selected option."""
        # Clear previous frames
        """
        for widget in self.winfo_children():
            if isinstance(widget, CTkFrame) and widget != self.image_source_frame:
                widget.destroy()


        if self.user_input_data.image_source != selection:
            self.user_input_data.import_files = None
            self.user_input_data.number_of_frames = None

        if selection == File_Source_Options[0]:
            self.setup_filesystem_frame()
        elif selection == File_Source_Options[1]:
            self.setup_cv2_videocapture_frame()
        elif selection == File_Source_Options[2]:
            self.setup_genlcam_frame()
        """
        self.user_input_data.image_source = selection

    def update_image_source(self, *args):
        self.user_input_data.image_source = self.image_source.get_value()

    def update_wait_time(self, *args):
        self.user_input_data.wait_time = self.wait_time.get_value()

    def update_edgefinder(self, *args):
        self.user_input_data.edgefinder = self.edgefinder.get_value()

    def setup_choose_files_frame(self):
        """Set up the choose files frame and its components."""
        self.choose_files_frame = CTkFrame(self, fg_color="transparent")
        self.choose_files_frame.grid(pady=5)
        self.setup_component_label(self.choose_files_frame, "Image Files: ")
        self.choose_files_button = CTkButton(
            self.choose_files_frame,
            text="Choose File(s)",
            command=self.select_files,
            height=30
        )
        self.choose_files_button.grid()
    
    def setup_component_label(self, frame, text):
        label = CTkLabel(frame, text=text, font=("Roboto", 16, "bold"), width=150, anchor="w")
        label.grid()

    def select_files(self):      
        # Filter out None or invalid file types
        filetypes = [
            ("Image Files", "*.png"),
            ("Image Files", "*.jpg"),
            ("Image Files", "*.jpeg"),
            ("Image Files", "*.gif"),
            ("Image Files", "*.bmp"),
            ("All Files", "*.*")
        ]

        self.user_input_data.import_files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=filetypes,
            initialdir=PATH_TO_SCRIPT
        )

        self.current_index = 0

        num_files = len(self.user_input_data.import_files)
        self.user_input_data.number_of_frames = num_files

        if num_files > 0:
            self.choose_files_button.configure(
                text=f"{num_files} File(s) Selected")

            if num_files > 1:
                # If number of files bigger than 0, give user an opportunity to enter the frame interval
                self.frame_interval_frame.grid(pady=5)
            else:
                self.frame_interval_frame.grid_forget()

        else:
            self.frame_interval_frame.grid_forget()
            self.choose_files_button.configure(text="Choose File(s)")  # Reset if no files were chosen
            messagebox.showinfo("No Selection", "No files were selected.")