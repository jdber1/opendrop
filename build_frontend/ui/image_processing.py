from customtkinter import CTk, CTkFrame, CTkButton, CTkLabel
from PIL import Image, ImageTk  # You need to install Pillow for image handling
import os


class ImageApp(CTk):
    def __init__(self):
        super().__init__()

        # Set window title and size
        self.title("Image Processing Application")
        self.geometry("800x600")

        # Create main frame
        self.main_frame = CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Image display area
        self.image_label = CTkLabel(
            self.main_frame, text="Image will be displayed here", fg_color="lightgrey", width=400, height=300)
        self.image_label.pack(pady=10)

        # Drop region button
        self.drop_region_button = CTkButton(
            self.main_frame, text="Set Drop Region", command=self.set_drop_region)
        self.drop_region_button.pack(pady=5)

        # Needle region button
        self.needle_region_button = CTkButton(
            self.main_frame, text="Set Needle Region", command=self.set_needle_region)
        self.needle_region_button.pack(pady=5)

        # Load images from the directory
        self.image_paths = self.load_images()  # Load all images
        self.current_index = 0  # To keep track of the currently displayed image

        # Previous and Next buttons
        self.prev_button = CTkButton(
            self.main_frame, text="Previous", command=self.show_previous_image)
        self.prev_button.pack(side="left", padx=20)

        self.next_button = CTkButton(
            self.main_frame, text="Next", command=self.show_next_image)
        self.next_button.pack(side="right", padx=20)

        # Load the first image by default if available
        if self.image_paths:
            # Load the first image by default
            self.load_image(self.image_paths[self.current_index])

        # Initialize current image
        self.current_image = None

    def load_images(self):
        """Load all images from the specified directory and return their paths."""
        directory = "experimental_data_set"  # Specify your directory here
        # List of supported image extensions
        supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp')

        # Check if the directory exists
        if not os.path.exists(directory):
            print(f"Directory '{directory}' does not exist.")
            return []

        # Load all images from the directory
        images = [f for f in os.listdir(
            directory) if f.lower().endswith(supported_extensions)]
        # Return the full paths of the images
        return [os.path.join(directory, img) for img in images]

    def load_image(self, selected_image):
        """Load and display the selected image."""
        # Use the selected image path directly
        print("image: ", selected_image)  # Check the constructed path
        try:
            self.current_image = Image.open(selected_image)  # Load the image
            self.display_image()  # Display the image
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")

    def display_image(self):
        """Display the currently loaded image."""
        if self.current_image:
            # Resize and display the image
            resized_image = self.current_image.resize(
                (400, 300), Image.LANCZOS)

            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.configure(image=self.tk_image)
            self.image_label.image = self.tk_image  # Keep a reference

    def show_previous_image(self):
        """Show the previous image in the directory."""
        if self.image_paths:
            self.current_index = (self.current_index -
                                  1) % len(self.image_paths)  # Wrap around
            # Load the previous image
            self.load_image(self.image_paths[self.current_index])

    def show_next_image(self):
        """Show the next image in the directory."""
        if self.image_paths:
            self.current_index = (self.current_index +
                                  1) % len(self.image_paths)  # Wrap around
            # Load the next image
            self.load_image(self.image_paths[self.current_index])

    def set_drop_region(self):
        """Placeholder for setting drop region functionality."""
        print("Drop region set")  # Implement functionality as needed

    def set_needle_region(self):
        """Placeholder for setting needle region functionality."""
        print("Needle region set")  # Implement functionality as needed


# Run the application
if __name__ == "__main__":
    app = ImageApp()
    app.mainloop()
