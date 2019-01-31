import itertools
from typing import Tuple

import numpy as np

NEEDLE_TOL   = 1.e-4
NEEDLE_STEPS = 20


def get_needle_width_from_contours(needle_contours: Tuple[np.ndarray, np.ndarray]):
    """Return the width of the needle defined by `needle_contours`

    :param needle_contours: The two edges of the needle, this is an `np.ndarray` in the format:
                                [[[x0, y0], ..., [xn, yn]], [[x'0, y'0], ..., [x'm, y'm]]]
                            Where xi, yi correspond to the left edge of the needle and x'i, y'i, the right edge.
    :return: Diameter of the needle (in same units as `needle_profile`)
    """
    if len(needle_contours) != 2:
        raise ValueError(
            '`needle_profile` must contain only two contours (left and right edge of needle), got `{}` contour(s)'
            .format(len(needle_contours))
        )

    # Sort the points of each contour in ascending y coordinate.
    needle_contours = tuple(edge[edge[:, 1].argsort()] for edge in needle_contours)  # type: Tuple[np.ndarray, np.ndarray]

    p0 = needle_contours[0][0]

    # Translate the needle contours such that the top left point is at (0, 0)
    needle_contours = tuple(edge - p0 for edge in needle_contours)

    [x0, x1, theta] = _optimise_needle(needle_contours)

    needle_diameter = abs((x1 - x0) * np.sin(theta))

    return needle_diameter


def _optimise_needle(needle_contours: Tuple[np.ndarray, np.ndarray]) -> Tuple[float, float, float]:
    """
    :param needle_contours: The two edges of the needle, see `get_needle_width_from_contours()` doc
    :return: (x0, x1, theta) where:
        x0: needle left edge x-coordinate.
        x1: needle right edge x-coordinate.
        theta: angle of needle in radians where 0 is horizontal.
    """
    edge0 = needle_contours[0]
    edge1 = needle_contours[1]

    # First guess: needle is perfectly vertical and edges are perfectly straight.
    x0 = edge0[0][0]
    x1 = edge1[0][0]

    theta = np.pi/2

    params = np.array([x0, x1, theta])

    for step in itertools.count():
        residuals, jac = _build_resids_jac(needle_contours, *params)

        jtj = np.dot(jac.T, jac)
        jte = np.dot(jac.T, residuals)

        delta = -np.dot(np.linalg.inv(jtj), jte).T

        params += delta

        if (abs(delta/params) < NEEDLE_TOL).all() or step > NEEDLE_STEPS:
            break

    return tuple(params)


def _build_resids_jac(needle_profile, x0, x1, theta):
    edge0, edge1 = needle_profile

    edge0_res, edge0_jac = _edge_resids_jac(edge0, x0, theta)
    edge1_res, edge1_jac = _edge_resids_jac(edge1, x1, theta)

    residuals = np.hstack((edge0_res, edge1_res))

    num_points = edge0_jac.shape[0] + edge1_jac.shape[0]

    jac = np.zeros((num_points, 3))

    jac[:len(edge0_jac), :2] = edge0_jac
    jac[len(edge0_jac):, 0] = edge1_jac[:, 0]
    jac[len(edge0_jac):, 2] = edge1_jac[:, 1]

    return [residuals, jac]


def _edge_resids_jac(edge, x0, theta):
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)

    residuals = np.array([(point[0] - x0) * sin_theta - point[1] * cos_theta for point in edge])

    jac = np.array([
        [-sin_theta, (point[0] - x0) * cos_theta + point[1] * sin_theta] for point in edge
    ])

    return [residuals, jac]
