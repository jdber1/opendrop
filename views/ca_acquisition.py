from customtkinter import *
from tkinter import filedialog, messagebox
from PIL import Image

from utils.image_handler import ImageHandler
from utils.config import *
from utils.validators import *
from .component.option_menu import OptionMenu
from .component.integer_entry import IntegerEntry

IMAGE_FRAME_WIDTH = 600
IMAGE_FRAME_HEIGHT = 400

class CaAcquisition(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.user_input_data = user_input_data

        self.image_handler = ImageHandler()

        self.grid_rowconfigure(0, weight=1)

        self.input_fields_frame = CTkFrame(self)
        self.input_fields_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(
            10, 0))  # Left side for input fields

        image_acquisition_frame = CTkFrame(self.input_fields_frame)
        image_acquisition_frame.grid(sticky="nw", padx=15, pady=10)

        image_acquisition_frame.grid_columnconfigure(2, weight=1)

        self.image_source = OptionMenu(self, image_acquisition_frame, "Image source:",
                                            IMAGE_SOURCE_OPTIONS, self.update_image_source, rw=0, default_value=IMAGE_SOURCE_OPTIONS[2])

        self.setup_choose_files_frame(image_acquisition_frame)

        self.edgefinder = OptionMenu(
            self, image_acquisition_frame, "Edge finder:", EDGEFINDER_OPTIONS, self.update_edgefinder, rw=2)  # added by DS 31/5/21

        self.number_frames = IntegerEntry(
            self, image_acquisition_frame, "Number of frames:", None, rw=3, cl=0)
        self.wait_time = IntegerEntry(
            self, image_acquisition_frame, "Wait time (s):", self.update_wait_time, rw=4, cl=0)
        
        self.images_frame = CTkFrame(self)

    def update_image_source(self, *args):
        image_source = self.image_source.get_value()
        if image_source == IMAGE_SOURCE_OPTIONS[2]:
            self.choose_files_button.configure(state="normal")
            state="normal"
        else:
            self.choose_files_button.configure(state="disabled")

        self.user_input_data.image_source = self.image_source.get_value()

    def update_wait_time(self, *args):
        self.user_input_data.wait_time = self.wait_time.get_value()

    def update_edgefinder(self, *args):
        self.user_input_data.edgefinder = self.edgefinder.get_value()

    def setup_choose_files_frame(self, frame):
        self.choose_files_label = CTkLabel(frame, text="Image Files: ", width=150, anchor="w")
        self.choose_files_label.grid(row=1, column=0, sticky="w", padx=(5, 5), pady=(5, 5))

        self.choose_files_button = CTkButton(
            frame,
            text="Choose File(s)",
            command=self.select_files,
            width=150,
        )
        self.choose_files_button.grid(row=1, column=1, sticky="w", padx=(5, 5), pady=(5, 5))
    

    def select_files(self):
        # Clear previous images
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
            self.choose_files_button.configure(
                text=f"{num_files} File(s) Selected")

            self.images_frame = CTkFrame(self)
            self.images_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=(10, 0))

            self.initialize_image_display(self.images_frame)

        else:
            self.choose_files_button.configure(text="Choose File(s)")  # Reset if no files were chosen
            messagebox.showinfo("No Selection", "No files were selected.")


    def initialize_image_display(self, frame):
        display_frame = CTkFrame(frame)
        display_frame.grid(sticky="nsew", padx=15, pady=(10, 0))

        self.image_label = CTkLabel(display_frame, text="", fg_color="lightgrey", width=IMAGE_FRAME_WIDTH, height=IMAGE_FRAME_HEIGHT)
        self.image_label.grid(padx=10, pady=(10, 5))

        file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
        self.name_label = CTkLabel(display_frame, text=file_name)
        self.name_label.grid()

        self.image_navigation_frame = CTkFrame(display_frame)
        self.image_navigation_frame.grid(pady=20)

        self.prev_button = CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)

        self.index_entry = CTkEntry(self.image_navigation_frame, width=5)
        self.index_entry.grid(row=0, column=1, padx=5, pady=5)
        self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
        self.index_entry.insert(0, str(self.current_index + 1))

        self.navigation_label = CTkLabel(self.image_navigation_frame, text=f" of {self.user_input_data.number_of_frames}", font=("Arial", 12))
        self.navigation_label.grid(row=0, column=2, padx=5, pady=5)

        self.next_button = CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
        self.next_button.grid(row=0, column=3, padx=5, pady=5)

        self.load_image(self.user_input_data.import_files[self.current_index])

    def load_image(self, selected_image):
        """Load and display the selected image."""
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        """Display the currently loaded image."""
        width, height = self.current_image.size
        new_width, new_height = self.image_handler.get_fitting_dimensions(width, height, max_width=IMAGE_FRAME_WIDTH, max_height=IMAGE_FRAME_HEIGHT)
        self.tk_image = CTkImage(self.current_image, size=(new_width, new_height))
        self.image_label.configure(image=self.tk_image)
        # Keep a reference to avoid garbage collection
        self.image_label.image = self.tk_image

    def change_image(self, direction):
        """Change the currently displayed image based on the direction."""
        if self.user_input_data.import_files:
            self.current_index = (
                self.current_index + direction) % self.user_input_data.number_of_frames
            # Load the new image
            self.load_image(
                self.user_input_data.import_files[self.current_index])
            self.update_index_entry()  # Update the entry with the current index
            file_name = os.path.basename(
                self.user_input_data.import_files[self.current_index])
            self.name_label.configure(text=file_name)

    def update_index_from_entry(self):
        """Update current index based on user input in the entry."""
        try:
            new_index = int(self.index_entry.get()) - \
                1  # Convert to zero-based index
            if 0 <= new_index < self.user_input_data.number_of_frames:
                self.current_index = new_index
                # Load the new image
                self.load_image(
                    self.user_input_data.import_files[self.current_index])
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

        self.update_index_entry()  # Update the entry display

    def update_index_entry(self):
        """Update the index entry to reflect the current index."""
        self.index_entry.delete(0, 'end')  # Clear the current entry
        # Insert the new index (1-based)
        self.index_entry.insert(0, str(self.current_index + 1))