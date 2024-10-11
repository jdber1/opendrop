from customtkinter import *

# Define your options and labels globally or pass them as parameters if preferred
AUTO_MANUAL_OPTIONS = ["Automated", "User-Selected"]  # Example options
LABEL_WIDTH = 200  # Adjust as needed


def create_user_input_fields(parent, user_input_data):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", text_color="black")
    label.pack(pady=(0, 10))  # Padding to separate from input fields

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(fill="both", padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Create StringVars to hold the input field values
    drop_region_var = StringVar(value=AUTO_MANUAL_OPTIONS[0])  # Set default to "Automated"
    needle_region_var = StringVar(value=AUTO_MANUAL_OPTIONS[0])  # Set default to "Automated"
    drop_density_var = StringVar()
    needle_diameter_var = StringVar()
    continuous_density_var = StringVar()
    pixel_mm_var = StringVar()

    # Create input fields using custom styles
    drop_region_choice = create_option_menu(input_fields_frame, "Drop Region:", AUTO_MANUAL_OPTIONS, variable=drop_region_var)
    needle_region_choice = create_option_menu(input_fields_frame, "Needle Region:", AUTO_MANUAL_OPTIONS, variable=needle_region_var)

    drop_density = create_float_entry(input_fields_frame, "Drop Density:", textvariable=drop_density_var)
    needle_diameter = create_float_entry(input_fields_frame, "Needle Diameter:", textvariable=needle_diameter_var)
    continuous_density = create_float_entry(input_fields_frame, "Continuous density (kg/m³):", textvariable=continuous_density_var)
    pixel_mm = create_float_entry(input_fields_frame, "Pixel to mm Ratio:", textvariable=pixel_mm_var)

    # Update user_input_data whenever the StringVar changes
    def update_user_input_data(*args):
        user_input_data["drop_region_choice"] = drop_region_var.get()
        user_input_data["needle_region_choice"] = needle_region_var.get()
        
        # Convert StringVar values to float, handle empty or invalid input
        try:
            user_input_data["drop_density"] = float(drop_density_var.get()) if drop_density_var.get() else None
            user_input_data["needle_diameter"] = float(needle_diameter_var.get()) if needle_diameter_var.get() else None
            user_input_data["continuous_density"] = float(continuous_density_var.get()) if continuous_density_var.get() else None
            user_input_data["pixel_mm"] = float(pixel_mm_var.get()) if pixel_mm_var.get() else None
        except ValueError:
            # Handle cases where conversion fails (e.g., input is not a valid float)
            user_input_data["drop_density"] = None
            user_input_data["needle_diameter"] = None
            user_input_data["continuous_density"] = None
            user_input_data["pixel_mm"] = None

    # Trace changes in StringVars
    drop_region_var.trace("w", update_user_input_data)
    needle_region_var.trace("w", update_user_input_data)
    drop_density_var.trace("w", update_user_input_data)
    needle_diameter_var.trace("w", update_user_input_data)
    continuous_density_var.trace("w", update_user_input_data)
    pixel_mm_var.trace("w", update_user_input_data)

    # Set the width of the input frames to 40% of the window width
    user_input_frame_width = int(parent.winfo_width() * 0.4)
    user_input_frame.configure(width=user_input_frame_width)

    return user_input_frame  # Return the frame for further use


def create_fitting_view_fields(parent, user_input_data):
    """Create user input fields and return the fitting."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="Statistical Output", text_color="black")
    label.pack(pady=20)

    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Creating checkbox variables
    var_residuals = BooleanVar(value=False)  # Default value for checkbox

    # Create checkboxes
    residuals_checkbox = CTkCheckBox(input_fields_frame, text="Residuals", variable=var_residuals)
    residuals_checkbox.pack(anchor='w', padx=5, pady=(5, 0))  # Anchored to the left with padding

    # Define a function to update user_input_data when checkbox state changes
    def update_residuals():
        user_input_data["residuals"] = var_residuals.get()  # True if checked, False if unchecked

    var_residuals.trace("w", lambda *args: update_residuals())

    return user_input_frame  # Return the frame if needed for further use


def create_analysis_method_fields(parent, user_input_data):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="Analysis Method", text_color="black")
    label.pack(pady=(0, 10))

    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Creating checkbox variables
    var_default_method = BooleanVar(value=True)  # Default value for checkbox

    # Initialize user_input_data with default value
    user_input_data["default_method"] = var_default_method.get()  # Store the initial state in user_input_data

    # Create checkboxes inside the input fields frame
    default_method_checkbox = CTkCheckBox(input_fields_frame, text="Default Method", variable=var_default_method)
    default_method_checkbox.pack(anchor='w', padx=5, pady=(5, 0))  # Anchored to the left with padding

    # Update user_input_data when checkbox state changes
    def update_default_method():
        user_input_data["default_method"] = var_default_method.get()  # True if checked, False if unchecked

    var_default_method.trace("w", lambda *args: update_default_method())  # Trace changes in the checkbox

    return user_input_frame  # Return the frame if needed for further use


def create_option_menu(parent, label_text, options, variable):
    """Create an option menu and return it."""
    # Create a frame for the option menu with yellow background
    frame = CTkFrame(parent)

    # Pack the frame with specified padding and centered
    frame.pack(pady=8, fill='x', padx=15)  # Use padding of 8 and fill horizontally

    # Center the frame in the parent
    frame_width = int(parent.winfo_width() * 0.85)  # Set frame width to 85% of parent width
    frame.configure(width=frame_width)  # Configure the frame's width

    # Create and pack the label
    label = CTkLabel(frame, text=label_text)
    label.pack(side='left', padx=(5, 10))  # Add padding to the right of the label

    # Create and pack the option menu
    option_menu = CTkOptionMenu(frame, variable=variable, values=options, width=200)
    option_menu.pack(side='right', padx=(0, 5))  # Add padding to the left of the option menu

    return option_menu  # Return the option menu


def create_float_entry(parent, label_text, textvariable):
    """Creates a float entry with a label."""
    frame = CTkFrame(parent)  # Create a frame for the float entry
    # Pack the frame with specified padding and centered
    frame.pack(pady=8, fill='x', padx=15)  # Use padding of 8 and fill horizontally

    # Center the frame in the parent
    frame_width = int(parent.winfo_width() * 0.85)  # Set frame width to 85% of parent width
    frame.configure(width=frame_width)  # Configure the frame's width

    label = CTkLabel(frame, text=label_text)
    label.pack(side='left', padx=(5, 10))  # Padding to the right of the label

    float_entry = CTkEntry(frame, width=200, textvariable=textvariable)  # Adjust to your custom entry style
    float_entry.pack(side='right', padx=(0, 5))  # Fill the frame

    return float_entry


if __name__ == "__main__":
    root = CTk()  # Create a CTk instance
    user_input_data = {}  # Initialize the dictionary to hold user input data
    user_input_frame = create_user_input_fields(root, user_input_data)  # Create user input fields
    user_input_frame.pack(fill="both", expand=True)  # Pack the user input frame

    root.mainloop()
