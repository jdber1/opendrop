import math

import numpy as np


# calculates the initial guess for the Bond number using method
# from Neeson et al. (see Mathematica Notebook - CalculatingBond.nb)
def bond_number(contour, apex_x, apex_y, apex_radius) -> float:
    r_z2 = scaled_radius_at_scaled_height(contour, apex_x, apex_y, apex_radius, 2)

    if r_z2 > 0:  # JB edit 26/3/15
        bond = 0.1756 * r_z2 ** 2 + 0.5234 * r_z2 ** 3 - 0.2563 * r_z2 ** 4  # interpolated from numerical data
        return bond

    r_z1 = scaled_radius_at_scaled_height(contour, apex_x, apex_y, apex_radius, 1)

    #    if r_z1 > 0: #JB edit 26/3/15
    #        bond = 5.819 * (r_z1 - 1) # interpolated from numerical data
    #        return bond

    # finally, if nether of these work, just use a naive guess
    return 0.15  # JB edit 26/3/2015


# fits a circle to the drop apex to calculate the (x, y) coordinate and apex radius R_0
def fit_circle(contour):
    sumX = np.double(0.0)
    sumY = np.double(0.0)
    sumX2 = np.double(0.0)
    sumY2 = np.double(0.0)
    sumXY = np.double(0.0)
    sumX3 = np.double(0.0)
    sumY3 = np.double(0.0)
    sumX2Y = np.double(0.0)
    sumXY2 = np.double(0.0)

    # Ensure at least 10 points are used, but no more than the number of contour points
    n = min(max(int(0.1*len(contour)), 10), len(contour))
    for k in range(0, n):
        xk, yk = contour[k]
        sumX += xk
        sumY += yk
        sumX2 += xk ** 2
        sumY2 += yk ** 2
        sumXY += xk * yk
        sumX3 += xk ** 3
        sumY3 += yk ** 3
        sumX2Y += (xk ** 2) * yk
        sumXY2 += xk * (yk ** 2)

    d11 = n * sumXY - sumX * sumY
    d20 = n * sumX2 - sumX ** 2
    d02 = n * sumY2 - sumY ** 2
    d30 = n * sumX3 - sumX2 * sumX
    d03 = n * sumY3 - sumY2 * sumY
    d21 = n * sumX2Y - sumX2 * sumY
    d12 = n * sumXY2 - sumX * sumY2

    # x = ((d30 + d12) * d02 - (d03 + d21) * d11) / (2 * (d20 * d02 - d11**2))
    # y = ((d03 + d21) * d20 - (d30 + d12) * d11) / (2 * (d20 * d02 - d11**2))
    # c = (sumX2 + sumY2 - 2 * x *sumX - 2 * y * sumY) / n

    # JB edit 24/11/15 to prevent overflow

    x = (0.5 * (d30 + d12) * d02 - 0.5 * (d03 + d21) * d11) / ((d20 * d02 - d11 ** 2))
    y = (0.5 * (d03 + d21) * d20 - 0.5 * (d30 + d12) * d11) / ((d20 * d02 - d11 ** 2))
    c = (sumX2 + sumY2 - 2 * x * sumX - 2 * y * sumY) / n

    R = math.sqrt(c + x ** 2 + y ** 2)

    return [x, y - R, R]


# calculates the radius of the pendant drop at z = height * R_0
def scaled_radius_at_scaled_height(contour, apex_x, apex_y, apex_radius, height):
    num_points = len(contour)
    if num_points == 0:
        return math.nan

    points_to_return = 5  # number of data points to average over

    z_value = apex_y + height * apex_radius

    if contour[-1][1] < z_value:
        # print('ERROR: not enough data points to accurately guess the Bond number')
        return math.nan

    index = 0
    while contour[index][1] < z_value:
        index += 1

    if (index < points_to_return) or ((num_points - index) < points_to_return):
        # print('ERROR: not enough data points to average over')
        return math.nan

    sum_radius = 0.0

    for k in range(index - points_to_return, index + points_to_return):
        sum_radius += abs(contour[k][0] - apex_x)

    scaled_radius = sum_radius / (2 * points_to_return * apex_radius)

    return scaled_radius
