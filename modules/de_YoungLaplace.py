#!/usr/bin/env python
#coding=utf-8

from math import pi
from numpy import sin, cos

# minimise calls to sin() and cos()
# defines the Young--Laplace system of differential equations to be solved
def ylderiv(x_vec, t, bond_number):
    x, y, phi, x_Bond, y_Bond, phi_Bond = x_vec
    x_s = cos(phi)
    y_s = sin(phi)
    phi_s = 2 - bond_number * y - y_s/x # - ->
    x_Bond_s = - y_s * phi_Bond
    y_Bond_s = x_s * phi_Bond
    phi_Bond_s = y_s * x_Bond / (x*x) - x_s * phi_Bond / x - y - bond_number * y_Bond
    return [x_s, y_s, phi_s, x_Bond_s, y_Bond_s, phi_Bond_s]

# defines the Young--Laplace system of differential equations to be solved
def dataderiv(x_vec, t, bond_number):
    x, y, phi, vol, sur = x_vec
    x_s = cos(phi)
    y_s = sin(phi)
    phi_s = 2 - bond_number * y - sin(phi)/x
    vol_s = pi * x**2 * y_s
    sur_s = 2 * pi * x
    return [x_s, y_s, phi_s, vol_s, sur_s]

# # defines the Young--Laplace system of differential equations to be solved
# def ylderiv(x_vec, t):
#     x, y, phi, x_Bond, y_Bond, phi_Bond = x_vec
#     x_s = cos(phi)
#     y_s = sin(phi)
#     phi_s = 2 - bond_number * y - sin(phi)/x
#     x_Bond_s = -sin(phi)*phi_Bond
#     y_Bond_s = cos(phi)*phi_Bond
#     phi_Bond_s = sin(phi) * x_Bond / (x*x) - cos(phi) * phi_Bond / x - y - bond_number * y_Bond
#     return [x_s, y_s, phi_s, x_Bond_s, y_Bond_s, phi_Bond_s]