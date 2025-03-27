import customtkinter as ctk
from PIL import ImageTk, Image
from utils.image_handler import ImageHandler
import os
from modules.select_regions import set_drop_region,set_surface_line, correct_tilt,user_ROI
from modules.classes import ExperimentalSetup, ExperimentalDrop, DropData, Tolerances

from modules.read_image import get_image

class ImageApp(ctk.CTkFrame):
    def __init__(self, parent, user_input_data):
        super().__init__(parent)

        # Initialize ImageHandler instance
        self.image_handler = ImageHandler()

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Image display area
        self.image_label = ctk.CTkLabel(
            self.main_frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.pack(pady=10)
 
        # Drop region button
        self.drop_region_button = ctk.CTkButton(
            # self.main_frame, text="Set Drop Region")
            self.main_frame, text="Set Drop Region", command=lambda: self.set_drop_region(user_input_data))
        # hide it for now

        # Needle region button
        self.needle_region_button = ctk.CTkButton(
            self.main_frame, text="Set Needle Region", command=self.set_needle_region)
        # hide it for now
        

        self.user_input_data = user_input_data
        # Load images from the directory
        self.image_paths = user_input_data.import_files  # Load all images
        self.current_index = 0  # To keep track of the currently displayed image

        # Previous and Next buttons
        self.prev_button = ctk.CTkButton(
            self.main_frame, text="Previous", command=lambda: self.change_image(-1))
        self.prev_button.pack(side="left", padx=20)

        self.next_button = ctk.CTkButton(
            self.main_frame, text="Next", command=lambda: self.change_image(1))
        self.next_button.pack(side="right", padx=20)

        if self.image_paths:
            # Load the first image by default
            self.load_image(self.image_paths[self.current_index])
        self.update_button_visibility()

    def load_images(self):
        """Load all images from the specified directory and return their paths."""
        directory = "experimental_data_set"
        return self.image_handler.get_image_paths(directory)

    def load_image(self, selected_image):
        """Load and display the selected image."""
        # print("Loading image: ", selected_image)  # Check the constructed path
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        """Display the currently loaded image."""
        width, height = self.current_image.size
        new_width, new_height = self.image_handler.get_fitting_dimensions(width, height)
        self.tk_image = ctk.CTkImage(self.current_image, size=(new_width, new_height))

        self.image_label.configure(image=self.tk_image)
        # Keep a reference to avoid garbage collection
        self.image_label.image = self.tk_image

    def change_image(self, direction):
        """Change the currently displayed image based on the direction."""
        if self.image_paths:
            self.current_index = (
                self.current_index + direction) % len(self.image_paths)  # Wrap around
            # Load the new image
            self.load_image(self.image_paths[self.current_index])

    def set_drop_region(self, user_input_data):
        """Placeholder for setting drop region functionality."""
        # Pass user_input_data to the function and update it
        raw_experiment = ExperimentalDrop()
        get_image(raw_experiment, user_input_data, 0) # save image in here...
        # set_drop_region(raw_experiment, user_input_data)
        user_ROI(self.image_paths[0], 'Select drop region',user_input_data )
     
        self.user_input_data.ift_drop_region = "Drop region set"
        print("Drop region set")

    def set_needle_region(self):
        """Placeholder for setting needle region functionality."""
        # set_drop_region(user_input_data)
        self.user_input_data.ift_needle_region = "Drop region set"
        print("Needle region set")


    def update_button_visibility(self):
        """Update the visibility of the drop region and needle region buttons based on user_input_data."""
        # Retrieve and print the values
        drop_region_value = self.user_input_data.user_input_fields.get("drop_region_choice")
        needle_region_value = self.user_input_data.user_input_fields.get("needle_region_choice")

        # Show or hide the Drop Region button
        if drop_region_value == "User-Selected":
            self.drop_region_button.pack(pady=5)
        else:
            self.drop_region_button.pack_forget()

        # Show or hide the Needle Region button
        if needle_region_value == "User-Selected":
            self.needle_region_button.pack(pady=5)
        else:
            self.needle_region_button.pack_forget()