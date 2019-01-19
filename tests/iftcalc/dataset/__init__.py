from pathlib import Path

import cv2
import numpy as np


class DropData:
    def __init__(self, path: Path):
        self.image = cv2.imread(str(path/'image.png'))
        self.drop_contour_annotation = np.load(path/'drop_contour_annotation.npy')
        self.drop_contour_fit = np.load(path/'drop_contour_fit.npy')
        self.profile_data = np.load(path/'profile_data.npy')
        self.params = np.load(path/'params.npy')
