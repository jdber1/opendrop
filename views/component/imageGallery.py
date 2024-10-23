import customtkinter as ctk
from PIL import ImageTk, Image
from utils.image_handler import ImageHandler
import os


class ImageGallery(ctk.CTkFrame):
    def __init__(self, parent, import_files):
        super().__init__(parent)

        # Initialize ImageHandler instance
        self.image_handler = ImageHandler()

        # Create main frame
        self.main_frame = ctk.CTkFrame(self, width=400, height=400)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid to make widgets resize with the window
        self.grid_rowconfigure(0, weight=1)  # Allow row 0 (image) to grow
        self.grid_columnconfigure(0, weight=1)  # Center widgets horizontally

        self.main_frame.grid_rowconfigure(0, weight=1)  # Center image
        self.main_frame.grid_rowconfigure(1, weight=0)  # Buttons below image
        self.main_frame.grid_columnconfigure(
            0, weight=1)  # Center horizontally
        self.main_frame.grid_columnconfigure(
            1, weight=1)  # Center horizontally

        # Image display area
        self.image_label = ctk.CTkLabel(
            self.main_frame, text="", fg_color="lightgrey")
        self.image_label.grid(
            row=0, column=0, columnspan=2, sticky="nsew")

        # Load images from the directory
        self.image_paths = import_files  # Load all images
        self.current_index = 0  # To keep track of the currently displayed image

        # Previous and Next buttons
        self.prev_button = ctk.CTkButton(
            self.main_frame, text="Previous", command=lambda: self.change_image(-1), width=80, height=25)
        self.prev_button.grid(row=1, column=0, padx=20, sticky="w")

        self.next_button = ctk.CTkButton(
            self.main_frame, text="Next", command=lambda: self.change_image(1), width=80, height=25)
        self.next_button.grid(row=1, column=1, padx=20, pady=2, sticky="e")

        # Load the first image by default if available
        if self.image_paths:
            self.load_image(self.image_paths[self.current_index])

    def load_images(self):
        """Load all images from the specified directory and return their paths."""
        directory = "experimental_data_set"
        return self.image_handler.get_image_paths(directory)

    def load_image(self, selected_image):
        """Load and display the selected image."""
        print("Loading image: ", selected_image)  # Check the constructed path
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        """Display the currently loaded image."""
        width, height = self.current_image.size
        new_width, new_height = self.image_handler.get_fitting_dimensions(
            width, height, max_height=250)
        self.tk_image = ctk.CTkImage(
            self.current_image, size=(new_width, new_height))

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
