from customtkinter import *
from utils.config import *
from views.component.option_menu import OptionMenu
from .float_entry import FloatEntry
from .float_combobox import FloatCombobox
from .check_button import CheckButton
# Define your options and labels globally or pass them as parameters if preferred
# AUTO_MANUAL_OPTIONS = ["Automated", "User-Selected"]  # Example options
LABEL_WIDTH = 200  # Adjust as needed

# ift [User Input]
def create_user_input_fields_ift(self, parent, user_input_data):
    """Create user input fields and return the frame containing them."""
    user_input_frame = CTkFrame(parent, fg_color="red")
    user_input_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Configure the grid for the user_input_frame to be resizable
    user_input_frame.grid_rowconfigure(0, weight=0)  # No resizing for the label row
    user_input_frame.grid_rowconfigure(1, weight=1)  # Allow resizing for the input fields row
    user_input_frame.grid_columnconfigure(0, weight=1)  # Allow resizing for the first column
    user_input_frame.grid_columnconfigure(1, weight=1)  # Allow resizing for the second column

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")  # Grid for label

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    # Configure the grid of the input_fields_frame to be resizable
    input_fields_frame.grid_rowconfigure(0, weight=1)  # Allow first row to resize
    input_fields_frame.grid_rowconfigure(1, weight=1)  # Allow second row to resize
    input_fields_frame.grid_rowconfigure(2, weight=1)  # Allow third row to resize
    input_fields_frame.grid_rowconfigure(3, weight=1)  # Allow fourth row to resize
    input_fields_frame.grid_rowconfigure(4, weight=1)  # Allow fifth row to resize
    input_fields_frame.grid_rowconfigure(5, weight=1)  # Allow sixth row to resize

    input_fields_frame.grid_columnconfigure(0, weight=1)  # Allow first column to resize
    input_fields_frame.grid_columnconfigure(1, weight=1)  # Allow second column to resize

    # Update the input value functions
    def update_drop_region_method(*args):
        user_input_data["drop_region_choice"] = self.drop_region_method.get_value()
        self.image_app.update_button_visibility()

    def update_needle_region_method(*args):
        user_input_data["needle_region_choice"] = self.needle_region_method.get_value()    
        self.image_app.update_button_visibility()

    def update_drop_density(*args):
        user_input_data["drop_density"] = self.drop_density_method.get_value() 

    def update_continuous_density(*args):
        user_input_data["continuous_density"] = self.continuous_density.get_value()       

    def update_needle_diameter(*args):
        user_input_data["needle_diameter"] = self.needle_diameter.get_value()       

    def update_pixel_mm(*args):
        user_input_data["pixel_mm"] = self.pixel_mm.get_value()      

    # Add input widgets with lambda functions for updates
    self.drop_region_method = OptionMenu(
        self, input_fields_frame, "Drop Region:", AUTO_MANUAL_OPTIONS, lambda *args: update_drop_region_method(*args), rw=0
    )
    self.needle_region_method = OptionMenu(
        self, input_fields_frame, "Needle Region:", AUTO_MANUAL_OPTIONS, lambda *args: update_needle_region_method(*args), rw=1
    )
    
    self.drop_density_method = FloatEntry(
        self, input_fields_frame, "Drop Density(kg/m³):", lambda *args: update_drop_density(*args), rw=2
    )
    self.continuous_density = FloatEntry(
        self, input_fields_frame, "Continuous density (kg/m):", lambda *args: update_continuous_density(*args), rw=3
    )
    self.needle_diameter = FloatEntry(
        self, input_fields_frame, "Needle Diameter(mm):", lambda *args: update_needle_diameter(*args), rw=4
    )
    self.pixel_mm = FloatEntry(
        self, input_fields_frame, "Pixel scale(px/mm):", lambda *args: update_pixel_mm(*args), rw=5
    )

    # Returning the user input frame
    return user_input_frame

# ift [CheckList Select]
def create_plotting_checklist_ift(self,parent,user_input_data):

    plotting_clist_frame = CTkFrame(parent,fg_color="green")
    plotting_clist_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(plotting_clist_frame, text="Statistical Output", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")  # Grid for label

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(plotting_clist_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    def update_residuals_boole(*args):
        user_input_data["residuals"] = self.residuals_boole.get_value()      
   
    self.residuals_boole = CheckButton(
        self, input_fields_frame, "Residuals", update_residuals_boole, rw=0, cl=0, state_specify='normal')
    
    return plotting_clist_frame

# ift [Analysis Methods]
def create_analysis_checklist_ift(self,parent,user_input_data):

    analysis_clist_frame = CTkFrame(parent)
    analysis_clist_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(analysis_clist_frame, text="Statistical Output", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")  # Grid for label

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(analysis_clist_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    def update_default_method_boole(*args):
        user_input_data["default_method"] = self.default_method_boole.get_value()   
    self.default_method_boole = CheckButton(
        self, input_fields_frame, "Default Method", update_default_method_boole, rw=0, cl=0)
    return analysis_clist_frame

def create_user_inputs_cm(self,parent,user_input_data):
    """Create user input fields and return the frame containing them."""
    # Create the user input frame
    user_input_frame = CTkFrame(parent)
    user_input_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15)

    # Create a label for the dynamic content
    label = CTkLabel(user_input_frame, text="User Inputs", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # Create a frame to hold all input fields
    input_fields_frame = CTkFrame(user_input_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")

    # Define update functions for each input
    def update_drop_id_method(*args):
        user_input_data.drop_ID_method = self.drop_ID_method.get_value()

    def update_threshold_method(*args):
        user_input_data.threshold_method = self.threshold_method.get_value()

    def update_threshold_value(*args):
        user_input_data.threshold_val = self.threshold_val.get_value()

    def update_baseline_method(*args):
        user_input_data.baseline_method = self.baseline_method.get_value()

    def update_density_outer(*args):
        user_input_data.density_outer = self.density_outer.get_value()

    def update_needle_diameter(*args):
        user_input_data.needle_diameter_mm = self.needle_diameter.get_value()

    # Create input fields with the associated update methods
    self.drop_ID_method = OptionMenu(
        self, input_fields_frame, "Drop ID method:", DROP_ID_OPTIONS,
        lambda *args: update_drop_id_method(*args), rw=0
    )
    self.threshold_method = OptionMenu(
        self, input_fields_frame, "Threshold value selection method:", THRESHOLD_OPTIONS,
        lambda *args: update_threshold_method(*args), rw=1
    )
    self.threshold_val = FloatEntry(
        self, input_fields_frame, "Threshold value (ignored if method=Automated):",
        lambda *args: update_threshold_value(*args), rw=2
    )
    self.baseline_method = OptionMenu(
        self, input_fields_frame, "Baseline selection method:", BASELINE_OPTIONS,
        lambda *args: update_baseline_method(*args), rw=3
    )
    self.density_outer = FloatEntry(
        self, input_fields_frame, "Continuous density (kg/m³):",
        lambda *args: update_density_outer(*args), rw=4
    )
    self.needle_diameter = FloatCombobox(
        self, input_fields_frame, "Needle diameter (mm):", NEEDLE_OPTIONS,
        lambda *args: update_needle_diameter(*args), rw=5
    )

    # Configure grid columns in the input fields frame
    input_fields_frame.grid_columnconfigure(0, minsize=LABEL_WIDTH)

    return user_input_frame

def create_plotting_checklist_cm(self, parent, user_input_data):
    """Create plotting checklist fields and return the frame containing them."""
    # Create the plotting checklist frame
    plotting_clist_frame = CTkFrame(parent)
    plotting_clist_frame.grid(row=1, column=2, columnspan=1, sticky="wens", padx=15, pady=15)

    # Create a label for the checklist
    label = CTkLabel(plotting_clist_frame, text="To view during fitting", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")  # Grid for label

    # Create a frame to hold all checkbox fields
    input_fields_frame = CTkFrame(plotting_clist_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    # Define update functions for each checkbox
    def update_residuals_boole(*args):
        user_input_data.residuals_boole = self.residuals_boole.get_value()

    def update_profiles_boole(*args):
        user_input_data.profiles_boole = self.profiles_boole.get_value()

    def update_ift_boole(*args):
        user_input_data.interfacial_tension_boole = self.IFT_boole.get_value()

    # Create check buttons with the associated update methods
    self.residuals_boole = CheckButton(
        self, input_fields_frame, "Residuals", update_residuals_boole, rw=0, cl=0, state_specify='normal'
    )
    self.profiles_boole = CheckButton(
        self, input_fields_frame, "Profiles", update_profiles_boole, rw=1, cl=0, state_specify='normal'
    )
    self.IFT_boole = CheckButton(
        self, input_fields_frame, "Physical quantities", update_ift_boole, rw=2, cl=0, state_specify='normal'
    )

    return plotting_clist_frame

def create_analysis_checklist_cm(self, parent, user_input_data):
    """Create analysis methods checklist and return the frame containing them."""
    # Create the analysis checklist frame
    analysis_clist_frame = CTkFrame(parent)
    analysis_clist_frame.grid(row=3, columnspan=4, sticky="wens", padx=15, pady=15)

    # Create a label for the analysis checklist
    label = CTkLabel(analysis_clist_frame, text="Analysis methods", font=("Roboto", 16, "bold"))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")  # Grid for label

    # Create a frame to hold all checkbox fields
    input_fields_frame = CTkFrame(analysis_clist_frame)
    input_fields_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="wens")  # Grid for input fields frame

    # Define update functions for each checkbox
    def update_tangent_boole(*args):
        user_input_data.analysis_methods_ca[TANGENT_FIT] = self.tangent_boole.get_value()

    def update_second_deg_polynomial_boole(*args):
        user_input_data.analysis_methods_ca[POLYNOMIAL_FIT] = self.second_deg_polynomial_boole.get_value()

    def update_circle_boole(*args):
        user_input_data.analysis_methods_ca[CIRCLE_FIT] = self.circle_boole.get_value()

    def update_ellipse_boole(*args):
        user_input_data.analysis_methods_ca[ELLIPSE_FIT] = self.ellipse_boole.get_value()

    def update_YL_boole(*args):
        user_input_data.analysis_methods_ca[YL_FIT] = self.YL_boole.get_value()

    def update_ML_boole(*args):
        user_input_data.analysis_methods_ca[ML_MODEL] = self.ML_boole.get_value()

    # Create check buttons with the associated update methods
    self.tangent_boole = CheckButton(
        self, input_fields_frame, "First-degree polynomial fit", update_tangent_boole, rw=0, cl=0
    )
    self.second_deg_polynomial_boole = CheckButton(
        self, input_fields_frame, "Second-degree polynomial fit", update_second_deg_polynomial_boole, rw=1, cl=0
    )
    self.circle_boole = CheckButton(
        self, input_fields_frame, "Circle fit", update_circle_boole, rw=2, cl=0
    )
    self.ellipse_boole = CheckButton(
        self, input_fields_frame, "Ellipse fit", update_ellipse_boole, rw=0, cl=1
    )
    self.YL_boole = CheckButton(
        self, input_fields_frame, "Young-Laplace fit", update_YL_boole, rw=1, cl=1
    )
    self.ML_boole = CheckButton(
        self, input_fields_frame, "ML model", update_ML_boole, rw=2, cl=1
    )

    return analysis_clist_frame

if __name__ == "__main__":
    root = CTk()  # Create a CTk instance
    user_input_data = {}  # Initialize the dictionary to hold user input data
    user_input_frame = create_user_input_fields_ift(root, user_input_data)  # Create user input fields
    user_input_frame.pack(fill="both", expand=True)  # Pack the user input frame

    root.mainloop()
