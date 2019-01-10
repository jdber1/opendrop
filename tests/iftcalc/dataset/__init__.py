from pathlib import Path

import numpy as np


class DropData:
    def __init__(self, dir: Path):
        self.drop_contour_annotation = np.load(dir/'drop_contour_annotation.npy')
        self.drop_contour_fit = np.load(dir/'drop_contour_fit.npy')
        self.profile_data = np.load(dir/'profile_data.npy')
        self.params = np.load(dir/'params.npy')
