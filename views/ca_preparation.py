from customtkinter import *
import tkinter as tk

from utils.config import *
from views.component.option_menu import OptionMenu
from .component.float_entry import FloatEntry
from .component.float_combobox import FloatCombobox
from .component.check_button import CheckButton

class CaPreparation(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.user_input_data = user_input_data
        
        self.create_user_inputs()
        self.create_plotting_checklist()
        self.create_analysis_checklist()

    def create_user_inputs(self):
        user_input_frame = tk.LabelFrame(
            self, text="User inputs", padx=30, pady=10)
        user_input_frame.config(background=BACKGROUND_COLOR)
        user_input_frame.grid(row=1, column=0, columnspan=2,
                              sticky="wens", padx=15, pady=15)

        self.drop_ID_method = OptionMenu(
            self, user_input_frame, "Drop ID method:", DROP_ID_OPTIONS, self.update_drop_ID_method, rw=0)
        self.threshold_method = OptionMenu(
            self, user_input_frame, "Threshold value selection method:", THRESHOLD_OPTIONS, self.update_threshold_method, rw=1)
        self.threshold_val = FloatEntry(
            self, user_input_frame, "Threshold value (ignored if method=Automated):", self.update_threshold_val, rw=2, state_specify='normal')  # , label_width=LABEL_WIDTH)
        self.baseline_method = OptionMenu(
            self, user_input_frame, "Baseline selection method:", BASELINE_OPTIONS, self.update_baseline_method, rw=3)
        self.density_outer = FloatEntry(
            self, user_input_frame, "Continuous density (kg/m"u"\u00b3""):", self.update_density_outer, rw=4, state_specify='normal')  # , label_width=LABEL_WIDTH)
        self.needle_diameter = FloatCombobox(
            self, user_input_frame, "Needle diameter (mm):", NEEDLE_OPTIONS, self.update_needle_diameter, rw=5, state_specify='normal')  # , label_width=LABEL_WIDTH)

        user_input_frame.grid_columnconfigure(0, minsize=LABEL_WIDTH)

    def create_plotting_checklist(self):
        plotting_clist_frame = tk.LabelFrame(
            self, text="To view during fitting", padx=30, pady=10)  # , height=15)
        plotting_clist_frame.config(background=BACKGROUND_COLOR)
        plotting_clist_frame.grid(
            row=1, column=2, columnspan=1, sticky="wens", padx=15, pady=15)  # , rowspan=3

        self.residuals_boole = CheckButton(
            self, plotting_clist_frame, "Residuals", self.update_residuals_boole, rw=0, cl=0, state_specify='normal')
        self.profiles_boole = CheckButton(
            self, plotting_clist_frame, "Profiles", self.update_profiles_boole, rw=1, cl=0, state_specify='normal')
        self.IFT_boole = CheckButton(
            self, plotting_clist_frame, "Physical quantities", self.update_IFT_boole, rw=2, cl=0, state_specify='normal')
        
    def create_analysis_checklist(self):
        analysis_clist_frame = tk.LabelFrame(
            self, text="Analysis methods", padx=30, pady=10)  # , height=15)
        analysis_clist_frame.config(background=BACKGROUND_COLOR)
        analysis_clist_frame.grid(
            row=3, columnspan=4, sticky="wens", padx=15, pady=15)  # , rowspan=3

        self.tangent_boole = CheckButton(
            self, analysis_clist_frame, "First-degree polynomial fit", self.update_tangent_boole, rw=0, cl=0)
        self.second_deg_polynomial_boole = CheckButton(
            self, analysis_clist_frame, "Second-degree polynomial fit", self.update_second_deg_polynomial_boole, rw=1, cl=0)
        self.circle_boole = CheckButton(
            self, analysis_clist_frame, "Circle fit", self.update_circle_boole, rw=2, cl=0)
        self.ellipse_boole = CheckButton(
            self, analysis_clist_frame, "Ellipse fit", self.update_ellipse_boole, rw=0, cl=1)
        self.YL_boole = CheckButton(
            self, analysis_clist_frame, "Young-Laplace fit", self.update_YL_boole, rw=1, cl=1)
        self.ML_boole = CheckButton(
            self, analysis_clist_frame, "ML model", self.update_ML_boole, rw=2, cl=1)
        

    def update_drop_ID_method(self, *args):
        self.user_input_data.drop_ID_method = self.drop_ID_method.get_value()

    def update_threshold_method(self, *args):
        self.user_input_data.threshold_method = self.threshold_method.get_value()

    def update_threshold_val(self, *args):
        self.user_input_data.threshold_val = self.threshold_val.get_value()

    def update_baseline_method(self, *args):
        self.user_input_data.baseline_method = self.baseline_method.get_value()

    def update_density_outer(self, *args):
        self.user_input_data.density_outer = self.density_outer.get_value()

    def update_needle_diameter(self, *args):
        self.user_input_data.needle_diameter = self.needle_diameter.get_value()

    def update_residuals_boole(self, *args):
        self.user_input_data.residuals_boole = self.residuals_boole.get_value()

    def update_profiles_boole(self, *args):
        self.user_input_data.profiles_boole = self.profiles_boole.get_value()

    def update_IFT_boole(self, *args):
        self.user_input_data.IFT_boole = self.IFT_boole.get_value()

    def update_tangent_boole(self, *args):
        self.user_input_data.tangent_boole = self.tangent_boole.get_value()

    def update_second_deg_polynomial_boole(self, *args):
        self.user_input_data.second_deg_polynomial_boole = self.second_deg_polynomial_boole.get_value()

    def update_circle_boole(self, *args):
        self.user_input_data.circle_boole = self.circle_boole.get_value()  

    def update_ellipse_boole(self, *args):
        self.user_input_data.ellipse_boole = self.ellipse_boole.get_value()   

    def update_YL_boole(self, *args):
        self.user_input_data.YL_boole = self.YL_boole.get_value()

    def update_ML_boole(self, *args):
        self.user_input_data.ML_boole = self.ML_boole.get_value()        