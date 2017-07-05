from __future__ import print_function

from abc import abstractmethod

import numpy as np
import cv2
# import time
# import datetime

BLUR_SIZE = 3
VERSION_CV2 = cv2.__version__

class BasicExtractProfile(object):

    def image_crop(self, image, points):
        # return image[points[0][0]:points[0][1], points[1][0]:points[1][1]]
        # return image[points[0][1]:points[1][1], points[0][0]:points[1][0]]
        # imageUD = np.flipud(image)
        # pixels are referenced as image[y][x] - row major order
        return image[np.int64(points[0][1]):np.int64(points[1][1]), np.int64(points[0][0]):np.int64(points[1][0])]

    def extract_drop_profile(self, raw_experiment, user_inputs):
        profile_crop = self.image_crop(raw_experiment.image, user_inputs.drop_region)
        # profile_edges = detect_edges(profile_crop, raw_experiment, user_inputs.drop_region)
        # profile, raw_experiment.ret = detect_edges(profile_crop, raw_experiment, user_inputs.drop_region)
        profile, raw_experiment.ret = self.detect_edges(profile_crop, raw_experiment, user_inputs.drop_region, -1, 1)
        raw_experiment.drop_data = profile[0]

        needle_crop = self.image_crop(raw_experiment.image, user_inputs.needle_region)
        raw_experiment.needle_data, ret = self.detect_edges(needle_crop, raw_experiment, user_inputs.needle_region, raw_experiment.ret, 2)



        # # detect needle edges
        # needle_crop = image_crop(raw_experiment.image, user_inputs.needle_region)
        # raw_experiment.needle_data = detect_edges(needle_crop, user_inputs.needle_region)

    @abstractmethod
    def detect_edges(self, image, raw_experiment, points, ret, n_contours): pass
