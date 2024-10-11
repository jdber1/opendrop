from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkImage
from PIL import ImageTk, Image
from utils.image_handler import ImageHandler
import os


class ImageGallery(CTkFrame):
    def __init__(self, parent, import_files):
        super().__init__(parent)

        # Initialize ImageHandler instance
        self.image_handler = ImageHandler()

        # Create main frame
        self.main_frame = CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Image display area
        self.image_label = CTkLabel(
            self.main_frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.pack(pady=10)

        # Load images from the directory
        self.image_paths = import_files  # Load all images
        self.current_index = 0  # To keep track of the currently displayed image

        # Previous and Next buttons
        self.prev_button = CTkButton(
            self.main_frame, text="Previous", command=lambda: self.change_image(-1))
        self.prev_button.pack(side="left", padx=20)

        self.next_button = CTkButton(
            self.main_frame, text="Next", command=lambda: self.change_image(1))
        self.next_button.pack(side="right", padx=20)

        # Load the first image by default if available
        if self.image_paths:
            # Load the first image by default
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
        resized_image = self.image_handler.resize_image(self.current_image)
        if resized_image:
            self.tk_image = ImageTk.PhotoImage(resized_image)
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
