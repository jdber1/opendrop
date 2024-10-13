#!/usr/bin/env python
#coding=utf-8
import math
import sys
import numpy as np


def initialise_parameters(experimental_drop, drop_data):
    omega_rotation = 0.0 # initial rotation angle (should revisit this)
    [x_apex, y_apex, radius_apex] = fit_circle(experimental_drop.drop_data)
    bond_number = calculate_Bond_number(experimental_drop.drop_data, x_apex, y_apex, radius_apex)
    drop_data.params = [x_apex, y_apex, radius_apex, bond_number, omega_rotation]
    # maybe calculate_max_s() to determine initial max_s - although current version can handle max_s being too small
    drop_data.max_s = 4.0


# fits a circle to the drop apex to calculate the (x, y) coordinate and apex radius R_0
def fit_circle(xypoints):
    lenpoints = len(xypoints)
    sumX = np.float64(0.0)
    sumY = np.float64(0.0)
    sumX2 = np.float64(0.0)
    sumY2 = np.float64(0.0)
    sumXY = np.float64(0.0)
    sumX3 = np.float64(0.0)
    sumY3 = np.float64(0.0)
    sumX2Y = np.float64(0.0)
    sumXY2 = np.float64(0.0)
    n = max(10, int(0.1 * lenpoints)) # ensure at least 10 points are used...
    if n > lenpoints:
        n = lenpoints # if there is not enough points take all points
    for k in range(0, n):
        xk, yk = xypoints[k]
        sumX += xk
        sumY += yk
        sumX2 += xk**2
        sumY2 += yk**2
        sumXY += xk * yk
        sumX3 += xk**3
        sumY3 += yk**3
        sumX2Y += (xk**2)*yk
        sumXY2 += xk*(yk**2)
    d11 = n * sumXY - sumX * sumY
    d20 = n * sumX2 - sumX**2
    d02 = n * sumY2 - sumY**2
    d30 = n * sumX3 - sumX2 * sumX
    d03 = n * sumY3 - sumY2 * sumY
    d21 = n * sumX2Y - sumX2 * sumY
    d12 = n * sumXY2 - sumX * sumY2
    x = ((d30 + d12) * d02 - (d03 + d21) * d11) / (2 * (d20 * d02 - d11**2))
    y = ((d03 + d21) * d20 - (d30 + d12) * d11) / (2 * (d20 * d02 - d11**2))
    c = (sumX2 + sumY2 - 2 * x *sumX - 2 * y * sumY) / n
    R = math.sqrt(c + x**2 + y**2)
    return [x, y - R, R]

# calculates the initial guess for the Bond number using method
# from Neeson et al. (see Mathematica Notebook - CalculatingBond.nb)
def calculate_Bond_number(xypoints, x_apex, y_apex, radius_apex):
    r_z2 = scaled_radius_at_scaled_height(xypoints, x_apex, y_apex, radius_apex, 2)
    if r_z2 > 0: #JB edit 26/3/15
        bond = 0.1756 * r_z2**2 + 0.5234 * r_z2**3 - 0.2563 * r_z2**4 # interpolated from numerical data
        return bond
    r_z1 = scaled_radius_at_scaled_height(xypoints, x_apex, y_apex, radius_apex, 1)
#    if r_z1 > 0: #JB edit 26/3/15
#        bond = 5.819 * (r_z1 - 1) # interpolated from numerical data
#        return bond
    # finally, if nether of these work, just use a naive guess
    return 0.15 #JB edit 26/3/2015

# calculates the radius of the pendant drop at z = height * R_0
def scaled_radius_at_scaled_height(xypoints, x_apex, y_apex, radius_apex, height):
    lenpoints = len(xypoints)
    points_to_return = 5 # number of data points to average over
    z_value = y_apex + height * radius_apex
    if xypoints[-1][1] < z_value:
        # print('ERROR: not enough data points to accurately guess the Bond number')
        # sys.exit(1)
        return -1
    index = 0
    while xypoints[index][1] < z_value:
        index += 1
    if (index < points_to_return) or ((lenpoints-index) < points_to_return):
#        print('ERROR: not enough data points to average over')
#        sys.exit(1)
        return -2
    sum_radius = 0.0
    for k in range(index-points_to_return,index+points_to_return):
        sum_radius += abs(xypoints[k][0] - x_apex)
    scaled_radius = sum_radius / (2 * points_to_return * radius_apex)
    return scaled_radius

# # determines the maximum required arc length, max_s
# def calculate_max_s(xypoints):
#     lenpoints = len(xypoints)
#     global s_left
#     global s_right
#     global s_max
#     s_max = 0.5 * smax
#     s_left = 0.
#     s_right = 0.
#     ptsConsider = 10
#     for i in range(lenpoints-ptsConsider,lenpoints):
#         x, y = xypoints[i]
#         minimumDistance(x, y, s_max)
#         s_max = max(s_max, s_left, s_right)
