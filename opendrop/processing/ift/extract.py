# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Tuple

import cv2
import numpy as np

from opendrop.utility import mycv


def apply_edge_detection(image: np.ndarray, gaussian_size: int = 3, canny_min: int = 30, canny_max: int = 60) \
        -> np.ndarray:
    image = image.copy()

    if len(image.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(image.shape) == 3 and image.shape[-1] == 3:
        image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError("'image' must be grayscale or rgb")

    image = cv2.GaussianBlur(image, (gaussian_size, gaussian_size), 0)
    image = cv2.Canny(image, canny_min, canny_max)

    return image


def extract_drop_profile(image: np.ndarray) -> np.ndarray:
    image = image.copy()

    if len(image.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(image.shape) == 3 and image.shape[-1] == 3:
        image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError("'image' must be grayscale or rgb")

    found_contours = mycv.find_contours(image)

    if len(found_contours) == 0:
        return np.empty((0, 2))

    # Assume the drop profile corresponds to the longest contour found (mycv.find_contours() returns found contours in
    # descending order of contour length)
    profile = found_contours[0]
    profile = mycv.squish_contour(profile)

    return profile


def extract_needle_profile(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    image = image.copy()

    if len(image.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(image.shape) == 3 and image.shape[-1] == 3:
        image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError("'image' must be grayscale or rgb")

    found_contours = mycv.find_contours(image)

    # Assume the needle side edges are the two longest contours found.
    needle_profile = tuple(found_contours[:2])

    # Insert placeholder edges if insufficient edges found, to maintain consistent return values.
    if len(needle_profile) == 0:
        needle_profile = (np.empty((0, 2)), np.empty((0, 2)))
    elif len(needle_profile) == 1:
        needle_profile = (needle_profile[0], np.empty((0, 2)))

    return needle_profile
