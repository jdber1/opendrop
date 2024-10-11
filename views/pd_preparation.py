import customtkinter as ctk

from .component.preparation import create_analysis_method_fields, create_fitting_view_fields, create_user_input_fields
from .component.imageProcessing import ImageApp


class PdPreparation(ctk.CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.user_input_data = user_input_data

        # Configure the grid to allow expansion for both columns
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)  # Left column for input fields
        self.grid_columnconfigure(1, weight=1)  # Right column for ImageApp

        # Create the frame for organizing input fields on the left
        self.input_fields_frame = ctk.CTkFrame(self)
        self.input_fields_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(
            10, 0))  # Left side for input fields

        # Create a frame for the right side image processing
        self.image_app_frame = ctk.CTkFrame(self)
        self.image_app_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=(
            10, 0))  # Right side for ImageApp

        # Create user input fields and analysis fields on the left
        self.create_user_input_fields(self.input_fields_frame)
        self.create_analysis_method_fields(self.input_fields_frame)
        self.create_fitting_view_fields(self.input_fields_frame)

        # Instantiate the ImageApp on the right
        self.image_app = ImageApp(
            self.image_app_frame, self.user_input_data.import_files)
        # Pack the image app to fill the frame
        self.image_app.pack(fill="both", expand=True)

    def create_user_input_fields(self, parent_frame):
        """Create and pack user input fields into the specified parent frame."""
        user_input_frame = create_user_input_fields(parent_frame)
        # Adjust as needed for your layout
        user_input_frame.pack(fill="x", expand=True, pady=(10, 0))

    def create_analysis_method_fields(self, parent_frame):
        """Create and pack analysis method fields into the specified parent frame."""
        analysis_frame = create_analysis_method_fields(parent_frame)
        # Adjust padding and expansion as needed
        analysis_frame.pack(fill="x", expand=True, pady=(10, 0))

    def create_fitting_view_fields(self, parent_frame):
        """Create and pack fitting view fields into the specified parent frame."""
        fitting_view_frame = create_fitting_view_fields(parent_frame)
        # Pack fitting view fields
        fitting_view_frame.pack(fill="x", expand=True)

#     def open_image_processing_popup(self):
#         """Open ImageApp as a pop-up window."""
#         # Create a new Toplevel window
#         self.image_processing_window = ctk.CTkToplevel(self)
#         self.image_processing_window.title("Image Processing")  # Title of the pop-up window
#         self.image_processing_window.geometry("800x600")  # Size of the pop-up window

#         # Instantiate the ImageApp and pack it into the pop-up window
#         self.image_processing = ImageApp(self.image_processing_window)  # Pass the Toplevel window as the parent
#         self.image_processing.pack(fill="both", expand=True)  # Display the ImageApp in the pop-up window

#     def create_top_input_fields(self):
#         """Create the top user input fields and pack them into the layout."""
#         # Create a frame for the top input fields
#         self.top_input_frame = ctk.CTkFrame(self.input_fields_frame)
#         self.top_input_frame.pack(fill="x", padx=16, pady=(8, 8))  # Padding around the frame

#         # Create a frame for the user input fields, occupying 50% of the width
#         self.user_input_frame = ctk.CTkFrame(self.top_input_frame)
#         self.user_input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))  # User input fields on the left

#         # Configure the grid to maintain proportions
#         self.top_input_frame.grid_columnconfigure(0, weight=1)  # Allow user_input_frame to take space
#         self.top_input_frame.grid_columnconfigure(1, weight=1)  # Allow image_app_frame to take space

#         # Create a single input field in the user input frame
#         self.input_field = create_user_input_fields(self.user_input_frame)
#         self.input_field.grid(row=0, column=0, padx=10, pady=(10, 0))  # Add padding around the input field

#         # Create an instance of ImageApp in the top input frame
#         self.image_app = ImageApp(self.top_input_frame)
#         self.image_app.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 0))  # ImageApp on the right


#     def create_bottom_input_fields(self):
#         """Create the bottom user input fields and pack them into the layout."""
#         # Create a frame for the bottom input fields
#         self.bottom_input_frame = ctk.CTkFrame(self.input_fields_frame)
#         self.bottom_input_frame.pack(fill="both", padx=16, pady=(8, 8))  # Padding around the frame

#         # Create the analysis and fitting view fields
#         self.analysis_fields = create_analysis_method_fields(self.bottom_input_frame)  # Analysis method fields
#         self.analysis_fields.pack(fill="x", expand=True, pady=(0, 10))  # Pack analysis fields to fill 60% width

#         self.fitting_view_fields = create_fitting_view_fields(self.bottom_input_frame)  # Fitting view fields
#         self.fitting_view_fields.pack(fill="x", expand=True)  # Pack fitting view fields to fill 60% width


# # Note: Ensure that the create_user_input_fields, create_analysis_method_fields, and create_fitting_view_fields functions return properly configured frames or widgets.
