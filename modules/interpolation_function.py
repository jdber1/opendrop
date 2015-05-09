#!/usr/bin/env python
#coding=utf-8
import numpy as np

# cubic spline interpoation function
# http://en.wikipedia.org/wiki/Spline_interpolation
# y_1 = q (x_1),  y_2 = q (x_2) 
# k_1 = q'(x_1),  k_2 = q'(x_2)
# Delta_x = x_2 - x_1
# t = (x - x_1) / (x_2 - x_1)
def cubic_interpolation_function(y_1, y_2, k_1, k_2, Delta_x, t):
    a =  k_1 * Delta_x - (y_2 - y_1)
    b = -k_2 * Delta_x + (y_2 - y_1)
    q = (1 - t) * y_1 + t * y_2 + t * (1 - t) * (a * (1 - t) + b * t)
    return q

# linear spline interpoation function
# y_1 = q (x_1),  y_2 = q (x_2) 
# t = (x - x_1) / (x_2 - x_1)
def linear_interpolation_function(y_1, y_2, t):
    q = (1 - t) * y_1 + t * y_2
    return q