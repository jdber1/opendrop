#!/usr/bin/env python
# coding=utf-8
from modules.fitting.de_YoungLaplace import ylderiv
#from .interpolation_function import cubic_interpolation_function
from scipy.integrate import odeint

import numpy as np

from utils.config import *

class Tolerances(object):
    def __init__(self, delta_tol, gradient_tol, maximum_fitting_steps, objective_tol, arclength_tol, maximum_arclength_steps, needle_tol, needle_steps):
        self.DELTA_TOL = delta_tol
        self.GRADIENT_TOL = gradient_tol
        self.MAXIMUM_FITTING_STEPS = maximum_fitting_steps
        self.OBJECTIVE_TOL = objective_tol
        self.ARCLENGTH_TOL = arclength_tol
        self.MAXIMUM_ARCLENGTH_STEPS = maximum_arclength_steps
        self.NEEDLE_TOL = needle_tol
        self.NEEDLE_STEPS = needle_steps


# class ExperimentalSetup(object):
#     def __init__(self):
#         self.density_drop = None
#         self.density_outer = None
#         self.needle_diameter_m = None
#         self.plot_residuals = None
#         self.plot_profiles = None
#         self.plot_IFT = None
#         self.img_src = None
#         self.total_images = None
#         self.wait_time = None
#         self.save_images = None
#         self.filename = None

class ExperimentalSetup(object):
    def __init__(self):
        self.screen_resolution = None
        self.drop_ID_method = 'Automated'
        self.threshold_method = 'Automated'
        self.needle_region_choice = 'Automated'
        self.threshold_val = None
        self.baseline_method = 'Automated'
        self.edgefinder = None
        self.density_outer = None # contininous density
        self.needle_diameter_mm = None
        self.drop_density = None
        self.pixel_mm = None
        self.original_boole = 0
        self.cropped_boole = 0
        self.threshold_boole = 0
        self.image_source = "Local images"
        self.show_popup = 0
        self.number_of_frames = None
        self.wait_time = None
        self.save_images_boole = None
        self.filename = None
        self.time_string = None
        self.local_files = None
        self.drop_region = None
        self.needle_region = None
        self.import_files = None
        self.frame_interval = 0
        self.analysis_method_fields_cm = {}
        self.analysis_methods_ca = {TANGENT_FIT: False, POLYNOMIAL_FIT: False, CIRCLE_FIT: False, ELLIPSE_FIT: False, YL_FIT: False, ML_MODEL: False}
        self.analysis_methods_pd = {INTERFACIAL_TENSION: True}
        self.statistical_output = {}
        self.statistical_output_cm = {}
        self.ift_drop_region = None
        self.ift_needle_region = None
        self.ca_drop_region = None
        self.ca_baseline_region = None
        self.cv2_capture_num = None
        self.genlcam_capture_num = None
        self.output_directory = None

class ExperimentalDrop(object):
    def __init__(self):
        self.image = None
        self.cropped_image = None
        self.contour = None
        self.drop_contour = None
        self.contact_points = None
        self.contact_angles = {}
        self.needle_data = None
        self.surface_data = None
        self.ret = None
        self.time = None
        self.pixels_to_mm = None
        
        # self.time_full = None
        # self.filename = None
        # self.img_src = 2


class DropData(object):
    def __init__(self):
        self.previous_guess = None
        self.previous_params = None
        self._params = None
        self._max_s = None
        self._s_points = 200
        self.theoretical_data = None
        self.parameter_dimensions = 5
        self.residuals = None
        self.arc_lengths = None
        # self.fitted = False
        self.needle_diameter_pixels = None
        self.s_left = None
        self.s_right = None
        # self.s_0 = None
        # self.start_time = None
        # # self.rho_drop = None
        # # self.rho_outer = None
        # # # capPX = 206 # radius of the capillary in pixels
        # # # capM = 1.651 / 1000. # radius of capillary in meters
        # # # pix2m = capM / capPX
        # self.rho_drop = 1000.
        # self.rho_outer = 0.
        # self.pix2m = 0.000008
        # self.needle_diameter_pixels = None
        # self.needle_diameter_m = None
        # self.number_experiments = None
        # self.wait_time = None


    if 0:# interpolates the theoretical profile data
        def profile(self, s):
            if (s < 0):
                raise ValueError("s value outside domain")
            if (s > self.max_s):
                # if the profile is called outside of the current region, expand
                self.max_s = 1.2 * s # expand region to include s_max
            Delta_s = self.max_s / self.s_points
            n1 = int(s / Delta_s)
            n2 = n1 + 1
            t =  s / Delta_s - n1
            vec1 = np.array(self.theoretical_data[n1])
            vec2 = np.array(self.theoretical_data[n2])
            bond_number = self.bond()
            Dvec1 = np.array(ylderiv(vec1, 0, bond_number))
            Dvec2 = np.array(ylderiv(vec2, 0, bond_number))
            value_at_s = cubic_interpolation_function(vec1, vec2, Dvec1, Dvec2, Delta_s, t)
            return value_at_s

    # generates a new drop profile
    def generate_profile_data(self):
        if (self._max_s is not None) and (self._s_points is not None) and (self._params is not None):
        # if [self.max_s, self.s_points, self.params].all():
            # self.fitted = False
            # s_data_points = np.arange(0, self.max_s*(1+2/self.s_points), self.max_s/self.s_points)
            s_data_points = np.linspace(0, self.max_s, self.s_points + 1)

            x_vec_initial = [.000001, 0., 0., 0., 0., 0.]
            bond_number = self.bond()
            self.theoretical_data = odeint(ylderiv, x_vec_initial, s_data_points, args=(bond_number,))

    # # generates a new drop profile
    # def generate_profile_volume_area_data(self):
    #     s_data_points = np.linspace(0, self.max_s, self.s_points + 1)
    #     x_vec_initial = [.000001, 0., 0., 0., 0.]
    #     bond_number = self.bond()
    #     self.original_data = odeint(dataderiv, x_vec_initial, s_data_points, args=(bond_number,))[-1,-2:]

    #     # interpolates the theoretical profile data
    # def profile(self):
    #     s_needle = self.determine
    #     Delta_s = self.s_needle() / self.s_points
    #     n1 = int(s / Delta_s)
    #     n2 = n1 + 1
    #     t =  s / Delta_s - n1
    #     vec1 = np.array(self.theoretical_data[n1])
    #     vec2 = np.array(self.theoretical_data[n2])
    #     bond_number = self.bond()
    #     Dvec1 = np.array(ylderiv(vec1, 0, bond_number))
    #     Dvec2 = np.array(ylderiv(vec2, 0, bond_number))
    #     value_at_s = cubic_interpolation_function(vec1, vec2, Dvec1, Dvec2, Delta_s, t)
    #     return value_at_s

    # def s_needle(self):
    #     return 100


    # generate new profile when params are changed
    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, vector):
        if len(vector) != self.parameter_dimensions:
            raise ValueError("Parameter array incorrect dimensions")
        self._params = vector
        self.generate_profile_data() # generate new profile when the parameters are changed

    # generate new profile when max_s is changed
    @property
    def max_s(self):
        return self._max_s

    @max_s.setter
    def max_s(self, value):
        if value <= 0:
            raise ValueError("Maximum arc length must be positive")
        self._max_s = float(value)
        self.generate_profile_data() # generate new profile when the maximum arc length is changed

    # test validity of variable s_points + generate new profile when s_points are
    @property
    def s_points(self):
        return self._s_points

    @s_points.setter
    def s_points(self, value):
        if value <= 1:
            raise ValueError("Number of points must be positive")
        if not isinstance(value, int):
            raise ValueError("Number of points must be an integer")
        self._s_points = value
        self.generate_profile_data() # generate new profile when the maximum arc length is changed

    # def calculate_interfacial_tension(self):
    #     if self.fitted:
    #         GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia
    #         D_rho = self.rho_drop - self.rho_outer
    #         a_radius = self.apex_radius() * self.pix2m
    #         Bond = self.bond()
    #         gamma_IFT = D_rho * GRAVITY * a_radius**2 / Bond
    #         # return gamma_IFT
    #         gamma_IFT_mN = 1000 * gamma_IFT
    #         return gamma_IFT_mN
    #     else:
    #         print('ERROR: drop profile not yet fitted')
    #         return None

    # returns the Bond number
    def bond(self):
        return self.params[3]

    # returns the apex radius
    def apex_radius(self):
        return self.params[2]

    # # returns the pixel to meter conversion
    # def pixel_to_mm(self):
    #     pix2m = self.needle_diameter_mm / self.needle_diemeter_pixels
    #     return pix2m

    # # returns the pixel to meter conversion
    # def fitted_vol_area(self):
    #     s_needle = self.max_s
    #     s_data_points = np.linspace(0, s_needle, self.s_points + 1)
    #     # EPS = .000001 # need to use Bessel function Taylor expansion below
    #     bond_number = self.bond()
    #     x_vec_initial = [.000001, 0., 0., 0., 0.]
    #     vol_sur = odeint(dataderiv, x_vec_initial, s_data_points, args=(bond_number,))[-1,-2:]
    #     return vol_sur
