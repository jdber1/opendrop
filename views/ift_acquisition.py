from typing import Any
import os
from tkinter import filedialog, messagebox
from PIL import Image
from customtkinter import *

from utils.image_handler import ImageHandler
from utils.validators import *
from utils.config import *
from .component.ctk_input_popup import CTkInputPopup
from .component.ctk_table_popup import CTkTablePopup

class IftAcquisition(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.image_handler = ImageHandler()
        self.user_input_data = user_input_data
        self.current_index = 0

        self.frame_interval_var = StringVar()
        self.frame_interval_var.trace_add("write", self.update_frame_interval)

        self.image_source = StringVar(value=user_input_data.image_source)

        self.cv2_capture_num_var = StringVar(value=1)
        self.cv2_capture_num_var.trace_add("write", self.update_cv2_capture_num)

        self.genlcam_capture_num_var = StringVar(value=1)
        self.genlcam_capture_num_var.trace_add("write", self.update_genlcam_capture_num)

        self.setup_image_source_frame()
        self.setup_filesystem_frame()

        self.images_frame = CTkFrame(self)

    def setup_image_source_frame(self):
        self.image_source_frame = CTkFrame(self, fg_color="transparent")
        self.image_source_frame.pack(pady=(20, 5))
        self.setup_component_label(self.image_source_frame, "Image Source: ")
        # self.option_menu = CTkOptionMenu(self.image_source_frame,
        #                                  variable=self.image_source,
        #                                  values=FILE_SOURCE_OPTIONS_IFT,
        #                                  command=self.show_image_source_frame)
        self.option_menu = CTkOptionMenu(self.image_source_frame,
                                         variable=self.image_source,
                                         values=["Local images"],
                                         command=self.show_image_source_frame)
        self.option_menu.pack(side="left")

    def setup_choose_files_frame(self):
        self.choose_files_frame = CTkFrame(self, fg_color="transparent")
        self.choose_files_frame.pack(pady=5)
        self.setup_component_label(self.choose_files_frame, "Image Files: ")
        self.choose_files_button = CTkButton(
            self.choose_files_frame,
            text="Choose File(s)",
            command=self.select_files,
            height=30
        )
        self.choose_files_button.pack(side="left")

    def setup_filesystem_frame(self):
        self.setup_choose_files_frame()
        self.frame_interval_frame = CTkFrame(self, fg_color="transparent")
        self.setup_numberic_entry_pair(self.frame_interval_frame, "Frame Intervals:", self.frame_interval_var)

    def setup_videocapture_frame(self):
        self.videocapture_frame = CTkFrame(self, fg_color="transparent")
        self.videocapture_frame.pack(pady=5)
        self.setup_component_label(self.videocapture_frame, "VideoCapture: ")
        self.open_videocapture_button = CTkButton(self.videocapture_frame, text="None", command=self.open_videocapture_popup, height=30)
        self.open_videocapture_button.pack(side="left")

    def setup_camera_frame(self):
        self.camera_frame = CTkFrame(self, fg_color="transparent")
        self.camera_frame.pack(pady=5)
        self.setup_component_label(self.camera_frame, "Camera: ")
        self.open_videocapture_button = CTkButton(self.camera_frame, text="None", command=self.open_camera_popup, height=30)
        self.open_videocapture_button.pack(side="left")

    def setup_capture_num_frame(self, variable):
        numberic_entry_frame = CTkFrame(self, fg_color="transparent")
        numberic_entry_frame.pack(pady=5)
        self.setup_numberic_entry_pair(numberic_entry_frame, "Number of images:", variable)

    def setup_numberic_entry_pair(self, frame, label_text, variable):
        self.setup_component_label(frame, label_text)
        self.setup_numberic_entry(frame, variable)

    def setup_component_label(self, frame, text):
        label = CTkLabel(frame, text=text, width=150, anchor="w")
        label.pack(side="left")

    def setup_numberic_entry(self, frame, variable):
        numberic_validate_command = self.register(validate_numeric_input)
        entry = CTkEntry(
            frame,
            textvariable=variable,
            validate="key",
            validatecommand=(numberic_validate_command, '%P'),
            height=30
        )
        entry.pack(side="left")

    def select_files(self):
        self.images_frame.destroy()
        self.user_input_data.import_files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=IMAGE_TYPE,
            initialdir=PATH_TO_SCRIPT
        )
        self.current_index = 0
        num_files = len(self.user_input_data.import_files)
        self.user_input_data.number_of_frames = num_files

        if num_files > 0:
            self.choose_files_button.configure(text=f"{num_files} File(s) Selected")
            if num_files > 1:
                self.frame_interval_frame.pack(pady=5)
            else:
                self.frame_interval_frame.pack_forget()

            self.images_frame = CTkFrame(self)
            self.images_frame.pack(pady=10)
            self.initialize_image_display(self.images_frame)
        else:
            self.frame_interval_frame.pack_forget()
            self.choose_files_button.configure(text="Choose File(s)")
            messagebox.showinfo("No Selection", "No files were selected.")

    def initialize_image_display(self, frame):
        self.image_label = CTkLabel(frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.pack()
        file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
        self.name_label = CTkLabel(frame, text=file_name, font=("Arial", 10))
        self.name_label.pack()
        self.image_navigation_frame = CTkFrame(frame)
        self.image_navigation_frame.pack(pady=20)
        self.prev_button = CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
        self.prev_button.pack(side="left", padx=5, pady=5)
        self.index_entry = CTkEntry(self.image_navigation_frame, width=5)
        self.index_entry.pack(side="left", padx=5, pady=5)
        self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
        self.index_entry.insert(0, str(self.current_index + 1))
        self.navigation_label = CTkLabel(self.image_navigation_frame, text=f" of {self.user_input_data.number_of_frames}", font=("Arial", 12))
        self.navigation_label.pack(side="left", padx=5, pady=5)
        self.next_button = CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
        self.next_button.pack(side="left", padx=5, pady=5)
        self.load_image(self.user_input_data.import_files[self.current_index])

    def load_image(self, selected_image):
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        width, height = self.current_image.size
        new_width, new_height = self.image_handler.get_fitting_dimensions(width, height)
        self.tk_image = CTkImage(self.current_image, size=(new_width, new_height))
        self.image_label.configure(image=self.tk_image)
        self.image_label.image = self.tk_image

    def change_image(self, direction):
        if self.user_input_data.import_files:
            self.current_index = (self.current_index + direction) % self.user_input_data.number_of_frames
            self.load_image(self.user_input_data.import_files[self.current_index])
            self.update_index_entry()
            file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
            self.name_label.configure(text=file_name)

    def update_index_from_entry(self):
        try:
            new_index = int(self.index_entry.get()) - 1
            if 0 <= new_index < self.user_input_data.number_of_frames:
                self.current_index = new_index
                self.load_image(self.user_input_data.import_files[self.current_index])
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        self.update_index_entry()

    def update_index_entry(self):
        self.index_entry.delete(0, 'end')
        self.index_entry.insert(0, str(self.current_index + 1))

    def update_frame_interval(self, *args):
        self.user_input_data.frame_interval = self.frame_interval_var.get()

    def update_cv2_capture_num(self, *args):
        self.user_input_data.cv2_capture_num = self.cv2_capture_num_var.get()

    def update_genlcam_capture_num(self, *args):
        self.user_input_data.genlcam_capture_num = self.genlcam_capture_num_var.get()

    def show_image_source_frame(self, selection):
        for widget in self.winfo_children():
            if isinstance(widget, CTkFrame) and widget != self.image_source_frame:
                widget.destroy()

        if self.user_input_data.image_source != selection:
            self.user_input_data.import_files = None
            self.user_input_data.number_of_frames = None

        if selection == FILE_SOURCE_OPTIONS_IFT[0]:
            self.setup_filesystem_frame()
        elif selection == FILE_SOURCE_OPTIONS_IFT[1]:
            self.setup_cv2_videocapture_frame()
        elif selection == FILE_SOURCE_OPTIONS_IFT[2]:
            self.setup_genlcam_frame()

        self.user_input_data.image_source = selection

    def setup_cv2_videocapture_frame(self):
        self.setup_videocapture_frame()
        self.setup_capture_num_frame(self.cv2_capture_num_var)
        self.frame_interval_frame = CTkFrame(self, fg_color="transparent")
        self.frame_interval_frame.pack()
        self.setup_numberic_entry_pair(self.frame_interval_frame, "Frame Intervals:", self.frame_interval_var)

    def setup_genlcam_frame(self):
        self.setup_camera_frame()
        self.setup_capture_num_frame(self.genlcam_capture_num_var)
        self.frame_interval_frame = CTkFrame(self, fg_color="transparent")
        self.frame_interval_frame.pack()
        self.setup_numberic_entry_pair(self.frame_interval_frame, "Frame Intervals:", self.frame_interval_var)

    def open_videocapture_popup(self):
        popup = CTkInputPopup(self, title="VideoCapture Argument Input", prompt="Please enter the VideoCapture argument:", on_confirm=self.videocapture_popup_on_confirm)
        popup.grab_set()

    def videocapture_popup_on_confirm(self, value: Any):
        messagebox.showinfo("Warning", f"Fail to open '{value}'")

    def open_camera_popup(self):
        popup = CTkTablePopup(self, ["ID", "Vendor", "Model", "Name", "Interface", "Version"], None, self.camera_popup_on_row_select, "Choose Camera...")
        popup.grab_set()

    def camera_popup_on_row_select(self, row: Any):
        print("Selected row:", row)
        messagebox.showinfo("Selected row", f"Selected row: '{row}'")
