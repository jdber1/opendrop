#!/usr/bin/env python
# coding=utf-8

from de_YoungLaplace import dataderiv
from scipy.integrate import odeint

import numpy as np

GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia


def generate_full_data(extracted_data, raw_experiment, fitted_drop_data, user_inputs, i):
    extracted_data.time[i] = raw_experiment.time - extracted_data.initial_image_time
    extracted_data.gamma_IFT_mN[i] = calculate_IFT(fitted_drop_data, user_inputs)
    pix2mm = pixels_to_mm(fitted_drop_data, user_inputs)
    extracted_data.pixels_to_mm[i] = pix2mm
    vol_sur_pix = fitted_vol_area(fitted_drop_data)
    extracted_data.volume[i] = vol_sur_pix[0] * pix2mm**3 # volume in uL
    extracted_data.area[i] = vol_sur_pix[1] * pix2mm**2 # area in mm^2
    extracted_data.parameters[i] = fitted_drop_data.previous_params










def calculate_IFT(fitted_drop_data, user_inputs):
    Delta_rho = user_inputs.drop_density - user_inputs.continuous_density
    # Bond = fitted_drop_data.bond()  
    # print(fitted_drop_data.apex_radius())  
    # print(pixels_to_meter(fitted_drop_data, user_inputs))
    bond_number = fitted_drop_data.previous_params[3]
    a_radius_m = fitted_drop_data.previous_params[2] * pixels_to_mm(fitted_drop_data, user_inputs) * 1.e-3
    gamma_IFT = Delta_rho * GRAVITY * a_radius_m**2 / bond_number
    # return gamma_IFT
    gamma_IFT_mN = 1000 * gamma_IFT
    return gamma_IFT_mN

# returns the pixel to meter conversion
def pixels_to_mm(fitted_drop_data, user_inputs):
    needle_diameter_mm = user_inputs.needle_diameter_mm
    needle_diameter_pixels = fitted_drop_data.needle_diameter_pixels
    pix2mm = needle_diameter_mm / needle_diameter_pixels
    return pix2mm

def fitted_vol_area(fitted_drop_data):
    # s_needle = fitted_drop_data.max_s
    s_needle = max(abs(fitted_drop_data.arc_lengths))
    s_data_points = np.linspace(0, s_needle, fitted_drop_data.s_points + 1)
    # EPS = .000001 # need to use Bessel function Taylor expansion below
    # bond_number = fitted_drop_data.bond()
    a_radius_px = fitted_drop_data.previous_params[2]
    bond_number = fitted_drop_data.previous_params[3]
    x_vec_initial = [.000001, 0., 0., 0., 0.]
    vol_sur = odeint(dataderiv, x_vec_initial, s_data_points, args=(bond_number,))[-1,-2:]
    return (vol_sur * [a_radius_px**3, a_radius_px**2])
