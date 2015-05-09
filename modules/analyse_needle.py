#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import numpy as np
# import cv,cv2

def calculate_needle_diameter(raw_experiment, fitted_drop_data, tolerances):
    # [offset, needle_diameter, theta] = fit_needle(raw_experiment.needle_data, tolerances)
    # fitted_drop_data.needle_diameter = needle_diameter
    # fitted_drop_data.needle_diameter = fit_needle(raw_experiment.needle_data, tolerances)
    fitted_drop_data.needle_diameter_pixels = fit_needle(raw_experiment.needle_data, tolerances)

def fit_needle(needle_data, tolerances):
    # needle_data_1 = needle_data[0]
    # needle_data_2 = needle_data[1]
    # this routine fits the needle via numerical Levenberg--Marquardt
    # [X0, X1, theta] = optimise(data, tolerances)
    needle_data_shifted = [needle_data[0]-needle_data[0][0], needle_data[1]-needle_data[0][0]]
    [X0, X1, theta] = optimise_needle(needle_data_shifted, tolerances)
    needle_diameter = abs((X1 - X0) * np.sin(theta))
    return needle_diameter


def optimise_needle(needle_data, tolerances):
    X0 = needle_data[0][0][0]
    X1 = needle_data[1][0][0]
    theta = 1.57
    params = [X0, X1, theta]
    loop = True
    steps = 0
    while loop:
        [residuals, Jac] = build_resids_Jac(params[0], params[1], params[2], needle_data)
        JTJ = np.dot(Jac.T, Jac)
        JTe = np.dot(Jac.T, residuals)
        delta = -np.dot(np.linalg.inv(JTJ), JTe).T
        params = params + delta
        max_delta_params = max(abs(delta / params)[1:]) # dont look at first since param[0] ~= 0
        if (max_delta_params < tolerances.NEEDLE_TOL) or (steps > tolerances.NEEDLE_STEPS):
            loop = False
        steps += 1
    # print([steps, max_delta_params, params])
    return params

# def build_resids_Jac(X0, X1, theta, data):
#     [residuals0, Jac0] = resids_Jac(X0, theta, data[0])
#     [residuals1, Jac1] = resids_Jac(X1, theta, data[1])
#     total_points = Jac0.shape[1] + Jac1.shape[1]
#     residuals = np.zeros(total_points)
#     Jac = np.zeros((total_points, 3))
#     for i in range(Jac0.shape[1]):
#         residuals[i] = residuals0[i]
#         Jac[i][0] = Jac0[i][0]
#         Jac[i][1] = Jac0[i][1]
#     for j in range(Jac0.shape[1]):
#         residuals[i+j] = residuals1[j]
#         Jac[i+j][0] = Jac1[j][0]
#         Jac[i+j][2] = Jac1[j][1]
#     return [residuals, Jac]

def build_resids_Jac(X0, X1, theta, data):
    [residuals0, Jac0] = resids_Jac(X0, theta, data[0])
    [residuals1, Jac1] = resids_Jac(X1, theta, data[1])
    total_points = Jac0.shape[0] + Jac1.shape[0]
    residuals = np.zeros(total_points)
    Jac = np.zeros((total_points, 3))
    range0 = len(residuals0)
    range1 = len(residuals1)
    for i in range(range0):
        residuals[i] = residuals0[i]
        Jac[i][0] = Jac0[i][0]
        Jac[i][1] = Jac0[i][1]
    for j in range(range1):
        residuals[range0+j] = residuals1[j]
        Jac[range0+j][0] = Jac1[j][0]
        Jac[range0+j][2] = Jac1[j][1]
    return [residuals, Jac]


def resids_Jac(X0, theta, data):
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    sc2 = 2 * sin_theta * cos_theta
    om2cc = 1 - 2 * cos_theta**2
    residuals = np.array([(data[i][0] - X0) * sin_theta - data[i][1] * cos_theta for i in range(data.shape[0])])
    Jac = np.array([[-sin_theta, (data[i][0] - X0) * cos_theta + data[i][1] * sin_theta] for i in range(data.shape[0])])
    # Jac = [(data[i][0] - X0) * sin_theta - data[i][1] * cos_theta for i in range(data)]
    return [residuals, Jac]
