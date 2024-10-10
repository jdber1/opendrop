import customtkinter as ctk
from .component.preparation import create_analysis_method_fields, create_fitting_view_fields, create_user_input_fields
from .component.imageProcessing import ImageApp

class PdPreparation(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Create the frame for organizing input fields
        self.input_fields_frame = ctk.CTkFrame(self)
        self.input_fields_frame.pack(fill="both", expand=True, padx=15, pady=(10, 0))  # Frame for input fields

        # Create the top input fields (Image Processing button and user input fields)
        self.create_top_input_fields()

        # Create the bottom input fields (analysis and fitting view fields)
        self.create_bottom_input_fields()

    def open_image_processing_popup(self):
        """Open ImageApp as a pop-up window."""
        # Create a new Toplevel window
        self.image_processing_window = ctk.CTkToplevel(self)
        self.image_processing_window.title("Image Processing")  # Title of the pop-up window
        self.image_processing_window.geometry("800x600")  # Size of the pop-up window

        # Instantiate the ImageApp and pack it into the pop-up window
        self.image_processing = ImageApp(self.image_processing_window)  # Pass the Toplevel window as the parent
        self.image_processing.pack(fill="both", expand=True)  # Display the ImageApp in the pop-up window

    def create_top_input_fields(self):
        """Create the top user input fields and pack them into the layout."""
        # Create a frame for the top input fields
        self.top_input_frame = ctk.CTkFrame(self.input_fields_frame, fg_color='lightblue')
        self.top_input_frame.pack(fill="x", padx=15, pady=(10, 5))  # Padding bottom margin of 5

        # Create the Image Processing button
        self.image_source_button = ctk.CTkButton(self.top_input_frame, text="Image Processing", width=150, height=40, command=self.open_image_processing_popup)
        self.image_source_button.pack(side="left", padx=(0, 10))  # Place the button at the left side of the frame

        # Create user input fields in the top frame
        self.user_input_fields = create_user_input_fields(self.top_input_frame)  # User input fields
        self.user_input_fields.pack(side="left", fill="x", expand=True)  # Pack them next to the button

    def create_bottom_input_fields(self):
        """Create the bottom user input fields and pack them into the layout."""
        # Create a frame for the bottom input fields
        self.bottom_input_frame = ctk.CTkFrame(self.input_fields_frame, fg_color='lightgreen')
        self.bottom_input_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))  # Add padding for aesthetics

        # Create the analysis and fitting view fields
        self.analysis_fields = create_analysis_method_fields(self.bottom_input_frame)  # Analysis method fields
        self.analysis_fields.pack(side="left", fill="x", expand=True, padx=(0, 10))  # Pack analysis fields horizontally

        self.fitting_view_fields = create_fitting_view_fields(self.bottom_input_frame)  # Fitting view fields
        self.fitting_view_fields.pack(side="left", fill="x", expand=True)  # Pack fitting view fields horizontally

# Note: Ensure that the create_user_input_fields, create_analysis_method_fields, and create_fitting_view_fields functions return properly configured frames or widgets.
