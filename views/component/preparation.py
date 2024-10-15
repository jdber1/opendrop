from customtkinter import *
from utils.config import *
from views.component.option_menu import OptionMenu
from .float_entry import FloatEntry
from .float_combobox import FloatCombobox
from .check_button import CheckButton
# Define your options and labels globally or pass them as parameters if preferred
AUTO_MANUAL_OPTIONS = ["Automated", "User-Selected"]  # Example options
LABEL_WIDTH = 200  # Adjust as needed

# ift [User Input]
def create_user_input_fields_ift(self, parent, user_input_data):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", text_color="black")
    label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="w")  # Grid for label

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    # update the input value
    def update_drop_region_method(*args):
        user_input_data["drop_region_choice"] = self.drop_region_method.get_value()

    def update_needle_region_method(*args):
        user_input_data["needle_region_choice"] = self.needle_region_method.get_value()    

    def update_drop_density(*args):
        user_input_data["drop_density"] = self.drop_density_method.get_value() 

    def update_continuous_density(*args):
        user_input_data["continuous_density"] = self.continuous_density.get_value()       

    def update_needle_diameter(*args):
        user_input_data["needle_diameter"] = self.needle_diameter.get_value()       

    def update_pixel_mm(*args):
        user_input_data["pixel_mm"] = self.pixel_mm.get_value()      

    # Pass the callback methods using lambda
    self.drop_region_method = OptionMenu(
        self, input_fields_frame, "Drop Region:", AUTO_MANUAL_OPTIONS, lambda *args: update_drop_region_method(*args), rw=0
    )
    self.needle_region_method = OptionMenu(
        self, input_fields_frame, "Needle Region:", AUTO_MANUAL_OPTIONS, lambda *args: update_needle_region_method(*args), rw=1
    )
    
    self.drop_density_method = FloatEntry(
        self, input_fields_frame, "Drop Density:", lambda *args: update_drop_density(*args), rw=2
    )
    self.continuous_density = FloatEntry(
        self, input_fields_frame, "Continuous density (kg/m)", lambda *args: update_continuous_density(*args), rw=3
    )
    self.needle_diameter = FloatEntry(
        self, input_fields_frame, "Needle Diameter:", lambda *args: update_needle_diameter(*args), rw=4
    )
    self.pixel_mm = FloatEntry(
        self, input_fields_frame, "Pixel to mm Ratio:", lambda *args: update_pixel_mm(*args), rw=5
    )
    return user_input_frame

# ift [CheckList Select]
def create_plotting_checklist(self,parent,user_input_data):

    plotting_clist_frame = CTkFrame(parent)
    plotting_clist_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(plotting_clist_frame, text="Statistical Output", text_color="black")
    label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="w")  # Grid for label

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(plotting_clist_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    def update_residuals_boole(*args):
        user_input_data["residuals"] = self.residuals_boole.get_value()      
   
    self.residuals_boole = CheckButton(
        self, input_fields_frame, "Residuals", update_residuals_boole, rw=0, cl=0, state_specify='normal')
    
    return plotting_clist_frame

# ift [Analysis Methods]
def create_analysis_checklist(self,parent,user_input_data):

        analysis_clist_frame = CTkFrame(parent)
        analysis_clist_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

        # Create a label for the dynamic content
        label = CTkLabel(analysis_clist_frame, text="Statistical Output", text_color="black")
        label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="w")  # Grid for label

        # Create a frame to hold all input fields
        input_fields_frame = CTkFrame(analysis_clist_frame)
        input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

        def update_default_method_boole(*args):
            user_input_data["default_method"] = self.default_method_boole.get_value()   
        self.default_method_boole = CheckButton(
            self, input_fields_frame, "Default Method", update_default_method_boole, rw=0, cl=0)
        return analysis_clist_frame

# ca 
def create_user_inputs(parent):
    """Create user input fields for contact angle (CA) analysis and return the frame containing them."""
    # Create the main frame to contain the user input fields
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the section title
    label = CTkLabel(user_input_frame, text="User Inputs", text_color="black")
    label.pack(pady=(0, 10))  # Padding between the label and the input fields

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.pack(fill="both", padx=10, pady=(0, 10))

    # Set default values for dropdowns only
    default_drop_ID_method = DROP_ID_OPTIONS[0]  # Default to first option in DROP_ID_OPTIONS
    default_threshold_method = THRESHOLD_OPTIONS[1]  # Example: Set default to second option in THRESHOLD_OPTIONS
    default_baseline_method = BASELINE_OPTIONS[0]  # Default to first option in BASELINE_OPTIONS
    default_needle_diameter = NEEDLE_OPTIONS[1]  # Example: Set default to second option in NEEDLE_OPTIONS

    # Create the input fields with relevant options and entry boxes
    OptionMenu(input_fields_frame, "Drop ID method:", DROP_ID_OPTIONS, self.update_drop_ID_method, default_value=default_drop_ID_method)
    threshold_method = OptionMenu(input_fields_frame, "Threshold value selection method:", THRESHOLD_OPTIONS, self.update_threshold_method, default_value=default_threshold_method)
    
    # Leave threshold value empty (no default value set)
    threshold_val = FloatEntry(input_fields_frame, "Threshold value (ignored if method=Automated):", self.update_threshold_val, state_specify='normal')
    
    baseline_method = OptionMenu(input_fields_frame, "Baseline selection method:", BASELINE_OPTIONS, self.update_baseline_method, default_value=default_baseline_method)
    
    # Leave continuous density empty (no default value set)
    density_outer = FloatEntry(input_fields_frame, "Continuous density (kg/m³):", self.update_density_outer, state_specify='normal')
    
    needle_diameter = FloatCombobox(input_fields_frame, "Needle diameter (mm):", NEEDLE_OPTIONS, self.update_needle_diameter, state_specify='normal', default_value=default_needle_diameter)



    # self.drop_ID_method = OptionMenu(
    #     self, user_input_frame, "Drop ID method:", DROP_ID_OPTIONS, self.update_drop_ID_method, rw=0)
    # self.threshold_method = OptionMenu(
    #     self, user_input_frame, "Threshold value selection method:", THRESHOLD_OPTIONS, self.update_threshold_method, rw=1)
    # self.threshold_val = FloatEntry(
    #     self, user_input_frame, "Threshold value (ignored if method=Automated):", self.update_threshold_val, rw=2, state_specify='normal')  # , label_width=LABEL_WIDTH)
    # self.baseline_method = OptionMenu(
    #     self, user_input_frame, "Baseline selection method:", BASELINE_OPTIONS, self.update_baseline_method, rw=3)
    # self.density_outer = FloatEntry(
    #     self, user_input_frame, "Continuous density (kg/m"u"\u00b3""):", self.update_density_outer, rw=4, state_specify='normal')  # , label_width=LABEL_WIDTH)
    # self.needle_diameter = FloatCombobox(
    #     self, user_input_frame, "Needle diameter (mm):", NEEDLE_OPTIONS, self.update_needle_diameter, rw=5, state_specify='normal')  # , label_width=LABEL_WIDTH)

    # user_input_frame.grid_columnconfigure(0, minsize=LABEL_WIDTH)

def create_user_input_fields(self,parent, user_input_data):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent)
    user_input_frame.pack(fill="both", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", text_color="black")
    label.pack(pady=(0, 10))  # Padding to separate from input fields

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    # Padding around the input fields frame
    input_fields_frame.pack(fill="both", padx=10, pady=(0, 10))

    # Create StringVars to hold the input field values
    drop_region_var = StringVar(value=AUTO_MANUAL_OPTIONS[0])  # Set default to "Automated"
    needle_region_var = StringVar(value=AUTO_MANUAL_OPTIONS[0])  # Set default to "Automated"
    drop_density_var = StringVar()
    needle_diameter_var = StringVar()
    continuous_density_var = StringVar()
    pixel_mm_var = StringVar()

  
    # Create input fields using custom styles
    create_option_menu(input_fields_frame, "Drop Region:", AUTO_MANUAL_OPTIONS, variable=drop_region_var)
    create_option_menu(input_fields_frame, "Needle Region:", AUTO_MANUAL_OPTIONS, variable=needle_region_var)

    create_float_entry(input_fields_frame, "Drop Density:", textvariable=drop_density_var)
    create_float_entry(input_fields_frame, "Needle Diameter:", textvariable=needle_diameter_var)
    create_float_entry(input_fields_frame, "Continuous density (kg/m³):", textvariable=continuous_density_var)
    create_float_entry(input_fields_frame, "Pixel to mm Ratio:", textvariable=pixel_mm_var)

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
    # Padding around the input fields frame
    input_fields_frame.pack(padx=10, pady=(0, 10))

    # Creating checkbox variables
    var_residuals = BooleanVar(value=False)  # Default value for checkbox

    # Create checkboxes
    residuals_checkbox = CTkCheckBox(
        input_fields_frame, text="Residuals", variable=var_residuals)
    # Anchored to the left with padding
    residuals_checkbox.pack(anchor='w', padx=5, pady=(5, 0))

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
    # Padding around the input fields frame
    input_fields_frame.pack(padx=10, pady=(0, 10))

    # Creating checkbox variables
    var_default_method = BooleanVar(value=True)  # Default value for checkbox

    # Initialize user_input_data with default value
    user_input_data["default_method"] = var_default_method.get()  # Store the initial state in user_input_data

    # Create checkboxes inside the input fields frame
    default_method_checkbox = CTkCheckBox(
        input_fields_frame, text="Default Method", variable=var_default_method)
    # Anchored to the left with padding
    default_method_checkbox.pack(anchor='w', padx=5, pady=(5, 0))

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
    # Use padding of 8 and fill horizontally
    frame.pack(pady=8, fill='x', padx=15)

    # Center the frame in the parent
    # Set frame width to 85% of parent width
    frame_width = int(parent.winfo_width() * 0.85)
    frame.configure(width=frame_width)  # Configure the frame's width

    # Create and pack the label
    label = CTkLabel(frame, text=label_text)
    # Add padding to the right of the label
    label.pack(side='left', padx=(5, 10))

    # Create and pack the option menu
    option_menu = CTkOptionMenu(frame, variable=variable, values=options, width=200)
    option_menu.pack(side='right', padx=(0, 5))  # Add padding to the left of the option menu

    return option_menu  # Return the option menu


def create_float_entry(parent, label_text, textvariable):
    """Creates a float entry with a label."""
    frame = CTkFrame(parent)  # Create a frame for the float entry
    # Pack the frame with specified padding and centered
    # Use padding of 8 and fill horizontally
    frame.pack(pady=8, fill='x', padx=15)

    # Center the frame in the parent
    # Set frame width to 85% of parent width
    frame_width = int(parent.winfo_width() * 0.85)
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
