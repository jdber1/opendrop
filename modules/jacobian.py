#!/usr/bin/env python
#coding=utf-8
# from scipy.integrate import odeint
import numpy as np
import math
# import sys
# from classes import ExperimentalDrop, DropData, Tolerances

cos = np.cos
sin = np.sin
dot = np.dot
sqrt = math.sqrt
minv = np.linalg.inv

# calculates a Jacobian row for the data point xy = x, y
def rowJacobian(x, y, drop_data, tolerances):
    [xP, yP, RP, BP, wP] = drop_data.params
    # x, y = xy # extract the data points
    # s_0 = drop_data.s_0
    if ((x - xP) * cos(wP) - (y - yP) * sin(wP)) < 0:
        s_0 = drop_data.s_left
    else:
        s_0 = drop_data.s_right
    # if x < xP:
    #     s_0 = s_left
    # else:
    #     s_0 = s_right



    xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i = minimum_arclength(x, y, s_0, drop_data, tolerances) # functions at s* 
    if ((x - xP) * cos(wP) - (y - yP) * sin(wP)) < 0:
        drop_data.s_left = s_i
    else:
        drop_data.s_right = s_i
    # e_i = sqrt(e_r**2 + e_z**2)              # actual residual
    e_i = math.copysign(sqrt(e_r**2 + e_z**2), e_r)              # actual residual
    sgnx = math.copysign(1, ((x - xP) * cos(wP) - (y - yP) * sin(wP))) # calculates the sign for ddi_dX0
    ddi_dxP = -( e_r * sgnx * cos(wP) + e_z * sin(wP) ) / e_i             # derivative w.r.t. X_0 (x at apex)
    ddi_dyP = -(-e_r * sgnx * sin(wP) + e_z * cos(wP) ) / e_i                    # derivative w.r.t. Y_0 (y at apex)
    ddi_dRP = -( e_r * xs + e_z * ys) / e_i  # derivative w.r.t. RP (apex radius)
    ddi_dBP = - RP * (e_r * dx_dBs + e_z * dy_dBs) / e_i   # derivative w.r.t. Bo  (Bond number)
    ddi_dwP = (e_r * sgnx * (- (x - xP) * sin(wP) - (y - yP) * cos(wP)) + e_z * ( (x - xP) * cos(wP) - (y - yP) * sin(wP))) / e_i
    return [[ ddi_dxP, ddi_dyP, ddi_dRP, ddi_dBP, ddi_dwP], e_i]

# calculates the minimum theoretical point to the point (x,y)
def minimum_arclength(x, y, s_i, drop_data, tolerances):
    [xP, yP, RP, BP, wP] = drop_data.params # unpack parameters
    max_s = drop_data.max_s # unpack maximum arc length
    loop = True
    s_step = 0
    flag_bump = 0
    # f_i = 10000 # need to give this a more sensible value
    while loop:
        xs, ys, phis, dx_dBs, dy_dBs, dphi_dBs = drop_data.profile(s_i)
        e_r = abs((x - xP) * cos(wP) - (y - yP) * sin(wP)) - RP * xs
        e_z =    ((x - xP) * sin(wP) + (y - yP) * cos(wP)) - RP * ys
        dphi_ds = 2 - BP * ys - sin(phis) / xs
        s_iplus1 = s_i - f_Newton(e_r, e_z, phis, dphi_ds, RP)
        f_iplus1 = RP * (e_r * cos(phis) + e_z * sin(phis))
        s_step += 1
        if s_iplus1 < 0: # arc length outside integrated region
            s_iplus1 = 0
            flag_bump += 1
        # if s_iplus1 > max_s: # arc length outside integrated region
        #     s_iplus1 = max_s
        #     flag_bump += 1
        if flag_bump >= 2: # has already been pushed back twice - abort
            loop = False
        if abs(s_iplus1 - s_i) < tolerances.ARCLENGTH_TOL:
            loop = False
        # # this was to check if the residual was very small
        # if abs(f_iplus1 - f_i) < RESIDUAL_TOL:
        #     loop = False
        if s_step >= tolerances.MAXIMUM_ARCLENGTH_STEPS:
            loop = False
            print("s failed to converge in ", str(s_step), " steps...", str(s_iplus1))
        s_i = s_iplus1
        # f_i = f_iplus1
    # drop_data.s_0 = s_i
    drop_data.s_previous = s_i
    return [xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i]

# the function g(s) used in finding the arc length for the minimal distance
def f_Newton(e_r, e_z, phi, dphids, RP):
    f = - (e_r * cos(phi) + e_z * sin(phi)) / (RP + dphids * (e_r * sin(phi) - e_z * cos(phi)))
    return f




