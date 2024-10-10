from customtkinter import *

# Define your options and labels globally or pass them as parameters if preferred
AUTO_MANNUL_OPTIONS = ["Automated", "User-Selected"]  # Example options
LABEL_WIDTH = 200  # Adjust as needed

def create_user_input_fields(parent):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", text_color="black")
    label.pack(pady=(0, 10))  # Padding to separate from input fields

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(fill="both", padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Create input fields using custom styles
    drop_region = create_option_menu(input_fields_frame, "Drop Region:", AUTO_MANNUL_OPTIONS)
    needle_region = create_option_menu(input_fields_frame, "Needle Region:", AUTO_MANNUL_OPTIONS)
    drop_density = create_float_entry(input_fields_frame, "Drop Density:")
    needle_diameter = create_float_entry(input_fields_frame, "Needle Diameter:")
    continuous_density = create_float_entry(input_fields_frame, "Continuous density (kg/m³):")
    pixel_mm = create_float_entry(input_fields_frame, "Pixel to mm Ratio:")

    # Set the width of the input frames to 40% of the window width
    user_input_frame_width = int(parent.winfo_width() * 0.4)
    user_input_frame.configure(width=user_input_frame_width)

    return user_input_frame  # Return the frame for further use

def create_fitting_view_fields(parent):
    """Create user input fields and return the fitting."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="Analysis Methods", text_color="black")
    label.pack(pady=20)

    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Creating checkbox variables
    var_residuals = BooleanVar(value=False)  # Default value for checkbox

    # Create checkboxes
    residuals_checkbox = CTkCheckBox(input_fields_frame, text="Residuals", variable=var_residuals)
    residuals_checkbox.pack(anchor='w', padx=5, pady=(5, 0))  # Anchored to the left with padding

    return user_input_frame  # Return the frame if needed for further use

def create_analysis_method_fields(parent):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="To View During Fitting", text_color="black")
    label.pack(pady=(0, 10)) 

    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(padx=10, pady=(0, 10))  # Padding around the input fields frame

    # Creating checkbox variables
    var_default_method = BooleanVar(value=True)  # Default value for checkbox

    # Create checkboxes inside the input fields frame
    default_method_checkbox = CTkCheckBox(input_fields_frame, text="Default Method", variable=var_default_method)
    default_method_checkbox.pack(anchor='w', padx=5, pady=(5, 0))  # Anchored to the left with padding

    return user_input_frame  # Return the frame if needed for further use

def create_option_menu(parent, label_text, options):
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
    option_menu = CTkOptionMenu(frame, values=options, width=200)
    option_menu.pack(side='right', padx=(0, 5))  # Add padding to the left of the option menu

    return option_menu  # Return the option menu

def create_float_entry(parent, label_text):
    """Creates a float entry with a label."""
    frame = CTkFrame(parent)  # Create a frame for the float entry
    # Pack the frame with specified padding and centered
    frame.pack(pady=8, fill='x', padx=15)  # Use padding of 8 and fill horizontally

    # Center the frame in the parent
    frame_width = int(parent.winfo_width() * 0.85)  # Set frame width to 85% of parent width
    frame.configure(width=frame_width)  # Configure the frame's width

    label = CTkLabel(frame, text=label_text)
    label.pack(side='left', padx=(5, 10))  # Padding to the right of the label

    float_entry = CTkEntry(frame, width=200)  # Adjust to your custom entry style
    float_entry.pack(side='right', padx=(0, 5))  # Fill the frame

    return float_entry

if __name__ == "__main__":
    root = CTk()  # Create a CTk instance
    user_input_frame = create_user_input_fields(root)  # Create user input fields
    user_input_frame.pack(fill="both", expand=True)  # Pack the user input frame

    root.mainloop()  # Start the main loop
