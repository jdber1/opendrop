import customtkinter as ctk
from PIL import ImageTk, Image
from utils.image_handler import ImageHandler
import os
from modules.select_regions import set_drop_region,set_surface_line, correct_tilt,user_ROI
from modules.classes import ExperimentalSetup, ExperimentalDrop, DropData, Tolerances
from tkinter import messagebox
from modules.read_image import get_image

class ImageApp(ctk.CTkFrame):
    def __init__(self, parent, user_input_data, experimental_drop, application):
        super().__init__(parent)
        
        self.application = application
        self.user_input_data = user_input_data
        self.experimental_drop = experimental_drop

        # Initialize ImageHandler instance
        self.image_handler = ImageHandler()

        # Load images from the directory
        self.image_paths = user_input_data.import_files  # Load all images
        self.current_index = 0  # To keep track of the currently displayed image

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(padx=20, pady=20, sticky="nsew")  # Use grid instead of pack

        # Call the function to initialize the image display area and buttons
        self.initialize_image_display(self.main_frame)

        # Drop region button
        self.drop_region_button = ctk.CTkButton(
            self.main_frame, text="Set Drop Region", command=lambda: set_drop_region(experimental_drop, user_input_data))
        # self.drop_region_button.grid(row=1, column=0, pady=5)  # Change to grid

        # Needle region button
        if application == "IFT":
            self.needle_region_button = ctk.CTkButton(
                self.main_frame, text="Set Needle Region", command=self.set_needle_region)
        
        if application == "CA":
            # Baseline region button
            self.basline_region_button = ctk.CTkButton(
                self.main_frame, text="Set Baseline Region", command=lambda: set_surface_line(experimental_drop, user_input_data))

        self.update_button_visibility()

    def initialize_image_display(self, frame):
        """Initialize the image display and navigation buttons inside the provided frame."""
        # Create a display frame for the image and navigation
        display_frame = ctk.CTkFrame(frame)
        display_frame.grid(sticky="nsew", padx=15, pady=(10, 0))

        # Create an image label to show the current image
        self.image_label = ctk.CTkLabel(display_frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.grid(row=0, column=0, padx=10, pady=(10, 5))

        # Create a label to display the current image's filename
        file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
        self.name_label = ctk.CTkLabel(display_frame, text=file_name)
        self.name_label.grid(row=1, column=0)

        # Create a frame for image navigation controls
        self.image_navigation_frame = ctk.CTkFrame(display_frame)
        self.image_navigation_frame.grid(row=2, column=0, pady=20)

        # Previous button to go to the previous image
        self.prev_button = ctk.CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)

        # Input field for the current index of the image
        self.index_entry = ctk.CTkEntry(self.image_navigation_frame, width=5)
        self.index_entry.grid(row=0, column=1, padx=5, pady=5)
        self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
        self.index_entry.insert(0, str(self.current_index + 1))

        # Label to display the total number of images (e.g., "1 of 10")
        self.navigation_label = ctk.CTkLabel(self.image_navigation_frame, text=f" of {len(self.image_paths)}", font=("Arial", 12))
        self.navigation_label.grid(row=0, column=2, padx=5, pady=5)

        # Next button to go to the next image
        self.next_button = ctk.CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
        self.next_button.grid(row=0, column=3, padx=5, pady=5)

        # Load and display the image at the current index
        self.load_image(self.user_input_data.import_files[self.current_index])

    def load_images(self):
        """Load all images from the specified directory and return their paths."""
        directory = "experimental_data_set"
        return self.image_handler.get_image_paths(directory)

    def load_image(self, selected_image):
        """Load and display the selected image."""
        try:
            self.current_image = Image.open(selected_image)
            get_image(self.experimental_drop, self.user_input_data, self.current_index)
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


    def set_needle_region(self):
        """Placeholder for setting needle region functionality."""
        self.user_input_data.ift_needle_region = "Drop region set"
        print("Needle region set")

    def update_button_visibility(self):
        """Update the visibility of the drop region and needle region buttons based on user_input_data."""
        drop_region_value = self.user_input_data.drop_ID_method

        if self.application == "IFT":
            needle_region_value = self.user_input_data.needle_region_choice
            # Show or hide the Needle Region button
            if needle_region_value == "User-selected":
                self.needle_region_button.grid(row=2, column=0, pady=5)  # Use grid instead of pack
            else:
                self.needle_region_button.grid_forget()  # Remove from grid if not needed
        else:
            baseline_region_value = self.user_input_data.baseline_method
            # Show or hide the Baseline Region button
            if baseline_region_value == "User-selected":
                self.basline_region_button.grid(row=3, column=0, pady=5)  # Use grid instead of pack
            else:
                self.basline_region_button.grid_forget()  # Remove from grid if not needed

        # Show or hide the Drop Region button
        if drop_region_value == "User-selected":
            self.drop_region_button.grid(row=1, column=0, pady=5)  # Use grid instead of pack
        else:
            self.drop_region_button.grid_forget()  # Remove from grid if not needed

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