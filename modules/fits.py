#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn.cluster import OPTICS # DS 7/6/21 - for clustering algorithm
import time
import datetime

def perform_fits(experimental_drop, tangent=False, polynomial=False, circle=False, ellipse=False, YL=False):
    if tangent == True:
        from .polynomial_fit import polynomial_fit
        tangent_angles, tangent_CPs, tangent_lines, tangent_errors, tangent_timings = polynomial_fit(experimental_drop.drop_contour, polynomial_degree=1)
        experimental_drop.contact_angles['tangent fit'] = {}
        experimental_drop.contact_angles['tangent fit']['left angle'] = tangent_angles[0]
        experimental_drop.contact_angles['tangent fit']['right angle'] = tangent_angles[1]
        experimental_drop.contact_angles['tangent fit']['contact points'] = tangent_CPs
        experimental_drop.contact_angles['tangent fit']['tangent lines'] = tangent_lines
        experimental_drop.contact_angles['tangent fit']['errors'] = tangent_errors
        experimental_drop.contact_angles['tangent fit']['timings'] = tangent_timings
    if polynomial == True:
        from .polynomial_fit import polynomial_fit
        polynomial_angles, polynomial_CPs, polynomial_lines, polynomial_errors, polynomial_timings = polynomial_fit(experimental_drop.drop_contour, polynomial_degree=2)
        experimental_drop.contact_angles['polynomial fit'] = {}
        experimental_drop.contact_angles['polynomial fit']['left angle'] = polynomial_angles[0]
        experimental_drop.contact_angles['polynomial fit']['right angle'] = polynomial_angles[1]
        experimental_drop.contact_angles['polynomial fit']['contact points'] = polynomial_CPs
        experimental_drop.contact_angles['polynomial fit']['tangent lines'] = polynomial_lines
        experimental_drop.contact_angles['polynomial fit']['errors'] = polynomial_errors
        experimental_drop.contact_angles['polynomial fit']['timings'] = polynomial_timings
    if circle == True:
        from .circular_fit import circular_fit
        circle_angles, circle_center, circle_radius, circle_intercepts, circle_errors, circle_timings = circular_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles['circle fit'] = {}
        experimental_drop.contact_angles['circle fit']['left angle'] = circle_angles[0]
        experimental_drop.contact_angles['circle fit']['right angle'] = circle_angles[1]
        experimental_drop.contact_angles['circle fit']['baseline intercepts'] = circle_intercepts
        experimental_drop.contact_angles['circle fit']['circle center'] = circle_center
        experimental_drop.contact_angles['circle fit']['circle radius'] = circle_radius
        experimental_drop.contact_angles['circle fit']['errors'] = circle_errors
        experimental_drop.contact_angles['circle fit']['timings'] = circle_timings
    if ellipse == True:
        from .ellipse_fit import ellipse_fit
        ellipse_angles, ellipse_intercepts, ellipse_center, ellipse_ab, ellipse_rotation, ellipse_errors, ellipse_timings = ellipse_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles['ellipse fit'] = {}
        experimental_drop.contact_angles['ellipse fit']['left angle'] = ellipse_angles[0]
        experimental_drop.contact_angles['ellipse fit']['right angle'] = ellipse_angles[1]
        experimental_drop.contact_angles['ellipse fit']['baseline intercepts'] = ellipse_intercepts
        experimental_drop.contact_angles['ellipse fit']['ellipse center'] = ellipse_center
        experimental_drop.contact_angles['ellipse fit']['ellipse a and b'] = ellipse_ab
        experimental_drop.contact_angles['ellipse fit']['ellipse rotation'] = ellipse_rotation
        experimental_drop.contact_angles['ellipse fit']['errors'] = ellipse_errors
        experimental_drop.contact_angles['ellipse fit']['timings'] = ellipse_timings
    if YL == True:
        from .BA_fit import YL_fit
        YL_angles, YL_Bo, YL_baselinewidth, YL_volume, YL_shape, YL_baseline, YL_errors, sym_errors, YL_timings = YL_fit(experimental_drop.drop_contour)
        experimental_drop.contact_angles['YL fit'] = {}
        experimental_drop.contact_angles['YL fit']['left angle'] = YL_angles[0]
        experimental_drop.contact_angles['YL fit']['right angle'] = YL_angles[1]
        experimental_drop.contact_angles['YL fit']['bond number'] = YL_Bo
        experimental_drop.contact_angles['YL fit']['baseline width'] = YL_baselinewidth
        experimental_drop.contact_angles['YL fit']['volume'] = YL_volume
        experimental_drop.contact_angles['YL fit']['fit shape'] = YL_shape
        experimental_drop.contact_angles['YL fit']['baseline'] = YL_baseline
        experimental_drop.contact_angles['YL fit']['errors'] = YL_errors
        experimental_drop.contact_angles['YL fit']['symmetry errors'] = sym_errors
        experimental_drop.contact_angles['YL fit']['timings'] = YL_timings
