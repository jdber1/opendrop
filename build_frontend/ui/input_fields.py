from customtkinter import *
from component.preparation import create_user_input_fields, create_analysis_method_fields, create_fitting_view_fields


class InputFields:
    def __init__(self, parent):
        """Initialize the input fields by creating top and bottom input frames."""
        self.parent = parent  # Store reference to the parent container

        # Call methods to create the fields and layout
        self.create_top_input_fields()
        self.create_bottom_input_fields()

    def create_top_input_fields(self):
        """Create the top user input fields and pack them into the layout."""
        # Create a frame for the top user input fields
        self.top_input_frame = CTkFrame(self.parent, fg_color='red')
        # Padding bottom margin of 16
        self.top_input_frame.pack(fill="x", padx=15, pady=(0, 16))

        # Create user input fields in the top frame (row 1)
        self.top_user_input_fields_1 = create_user_input_fields(
            self.top_input_frame)  # First set
        self.top_user_input_fields_2 = create_analysis_method_fields(
            self.top_input_frame)  # Second set

        # Adjust the weight of the columns for resizing
        self.top_input_frame.grid_columnconfigure(
            0, weight=55)  # Adjust first column weight
        self.top_input_frame.grid_columnconfigure(
            1, weight=35)  # Adjust second column weight

        # Pack the two input field sets in the top input frame
        self.top_user_input_fields_1.pack(
            side="left", fill="both", expand=True, padx=(0, 24))  # First input set (55%)
        self.top_user_input_fields_2.pack(
            side="right", fill="both", expand=True, padx=(24, 0))  # Second input set (35%)

    def create_bottom_input_fields(self):
        """Create the bottom user input fields and pack them into the layout."""
        # Create a frame for the bottom user input field (row 2)
        self.bottom_input_frame = CTkFrame(self.parent)
        self.bottom_input_frame.pack(side="left", padx=(24, 24))

        # Create the third user input field set (row 2)
        self.bottom_user_input_fields = create_fitting_view_fields(
            self.bottom_input_frame)  # Third set

        # Pack the bottom user input field set
        self.bottom_user_input_fields.pack(pady=(0, 0))  # Align to the left


# Example usage
if __name__ == "__main__":
    root = CTk()  # Create a CTk instance
    dynamic_content = InputFields(root)  # Create the DynamicContent instance
    # Pack the dynamic content frame
    dynamic_content.pack(fill="both", expand=True)

    # Run the single command to set up input fields
    dynamic_content.run_input_fields()

    root.mainloop()  # Start the main loop
