#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function

from utils.config import *

def perform_fits(experimental_drop, tangent=False, polynomial=False, circle=False, ellipse=False, YL=False):
    if tangent == True:
        from modules.fitting.polynomial_fit import polynomial_fit
        tangent_angles, tangent_CPs, tangent_lines, tangent_errors, tangent_timings = polynomial_fit(experimental_drop.drop_contour, polynomial_degree=1)
        experimental_drop.contact_angles[TANGENT_FIT] = {}
        experimental_drop.contact_angles[TANGENT_FIT][LEFT_ANGLE] = tangent_angles[0]
        experimental_drop.contact_angles[TANGENT_FIT][RIGHT_ANGLE] = tangent_angles[1]
        experimental_drop.contact_angles[TANGENT_FIT]['contact points'] = tangent_CPs
        experimental_drop.contact_angles[TANGENT_FIT]['tangent lines'] = tangent_lines
        experimental_drop.contact_angles[TANGENT_FIT]['errors'] = tangent_errors
        experimental_drop.contact_angles[TANGENT_FIT]['timings'] = tangent_timings
    if polynomial == True:
        from modules.fitting.polynomial_fit import polynomial_fit
        polynomial_angles, polynomial_CPs, polynomial_lines, polynomial_errors, polynomial_timings = polynomial_fit(experimental_drop.drop_contour, polynomial_degree=2)
        experimental_drop.contact_angles[POLYNOMIAL_FIT] = {}
        experimental_drop.contact_angles[POLYNOMIAL_FIT][LEFT_ANGLE] = polynomial_angles[0]
        experimental_drop.contact_angles[POLYNOMIAL_FIT][RIGHT_ANGLE] = polynomial_angles[1]
        experimental_drop.contact_angles[POLYNOMIAL_FIT]['contact points'] = polynomial_CPs
        experimental_drop.contact_angles[POLYNOMIAL_FIT]['tangent lines'] = polynomial_lines
        experimental_drop.contact_angles[POLYNOMIAL_FIT]['errors'] = polynomial_errors
        experimental_drop.contact_angles[POLYNOMIAL_FIT]['timings'] = polynomial_timings
    if circle == True:
        from modules.fitting.circular_fit import circular_fit
        circle_angles, circle_center, circle_radius, circle_intercepts, circle_errors, circle_timings = circular_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles[CIRCLE_FIT] = {}
        experimental_drop.contact_angles[CIRCLE_FIT][LEFT_ANGLE] = circle_angles[0]
        experimental_drop.contact_angles[CIRCLE_FIT][RIGHT_ANGLE] = circle_angles[1]
        experimental_drop.contact_angles[CIRCLE_FIT]['baseline intercepts'] = circle_intercepts
        experimental_drop.contact_angles[CIRCLE_FIT]['circle center'] = circle_center
        experimental_drop.contact_angles[CIRCLE_FIT]['circle radius'] = circle_radius
        experimental_drop.contact_angles[CIRCLE_FIT]['errors'] = circle_errors
        experimental_drop.contact_angles[CIRCLE_FIT]['timings'] = circle_timings
    if ellipse == True:
        from modules.fitting.ellipse_fit import ellipse_fit
        ellipse_angles, ellipse_intercepts, ellipse_center, ellipse_ab, ellipse_rotation, ellipse_errors, ellipse_timings = ellipse_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles[ELLIPSE_FIT] = {}
        experimental_drop.contact_angles[ELLIPSE_FIT][LEFT_ANGLE] = ellipse_angles[0]
        experimental_drop.contact_angles[ELLIPSE_FIT][RIGHT_ANGLE] = ellipse_angles[1]
        experimental_drop.contact_angles[ELLIPSE_FIT]['baseline intercepts'] = ellipse_intercepts
        experimental_drop.contact_angles[ELLIPSE_FIT]['ellipse center'] = ellipse_center
        experimental_drop.contact_angles[ELLIPSE_FIT]['ellipse a and b'] = ellipse_ab
        experimental_drop.contact_angles[ELLIPSE_FIT]['ellipse rotation'] = ellipse_rotation
        experimental_drop.contact_angles[ELLIPSE_FIT]['errors'] = ellipse_errors
        experimental_drop.contact_angles[ELLIPSE_FIT]['timings'] = ellipse_timings
    if YL == True:
        from modules.fitting.BA_fit import YL_fit
        YL_angles, YL_Bo, YL_baselinewidth, YL_volume, YL_shape, YL_baseline, YL_errors, sym_errors, YL_timings = YL_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles[YL_FIT] = {}
        experimental_drop.contact_angles[YL_FIT][LEFT_ANGLE] = YL_angles[0]
        experimental_drop.contact_angles[YL_FIT][RIGHT_ANGLE] = YL_angles[1]
        experimental_drop.contact_angles[YL_FIT]['bond number'] = YL_Bo
        experimental_drop.contact_angles[YL_FIT]['baseline width'] = YL_baselinewidth
        experimental_drop.contact_angles[YL_FIT]['volume'] = YL_volume
        experimental_drop.contact_angles[YL_FIT]['fit shape'] = YL_shape
        experimental_drop.contact_angles[YL_FIT]['baseline'] = YL_baseline
        experimental_drop.contact_angles[YL_FIT]['errors'] = YL_errors
        experimental_drop.contact_angles[YL_FIT]['symmetry errors'] = sym_errors
        experimental_drop.contact_angles[YL_FIT]['timings'] = YL_timings
