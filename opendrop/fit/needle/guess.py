from typing import Sequence

import numpy as np

from .types import NeedleParam


def needle_guess(data: np.ndarray) -> Sequence[float]:
    params = np.empty(len(NeedleParam))

    cm = data.mean(axis=1)
    # Points relative to "centre of mass".
    data_cm = data - cm.reshape(2, 1)
    dists = np.linalg.norm(data_cm, axis=0)
    closest_cm = data_cm[:, np.argsort(dists)[0]]
    projection = (closest_cm.reshape(2, 1) * data_cm).sum(axis=0)

    edge1_mask = projection > 0
    edge1 = data[:, edge1_mask]
    edge1_dir = _guess_line_direction(edge1)
    edge1_perp = edge1_dir[::-1] * [1, -1]

    rotation = -np.arctan2(*edge1_dir)
    radius = np.abs(edge1_perp @ closest_cm.reshape(2, 1))
    center_x = cm[0]
    center_y = cm[1]

    params[NeedleParam.ROTATION] = rotation
    params[NeedleParam.RADIUS] = radius
    params[NeedleParam.CENTER_X] = center_x
    params[NeedleParam.CENTER_Y] = center_y

    return params


def _guess_line_direction(data: np.ndarray) -> np.ndarray:
    x0 = data[:, 0]
    dists = np.argsort(np.linalg.norm(data - x0.reshape(2, 1), axis=0))
    x1 = data[:, dists[-1]]

    return (x1 - x0)/np.linalg.norm(x1 - x0)
