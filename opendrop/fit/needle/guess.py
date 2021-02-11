from typing import Sequence
import math

import numpy as np
import scipy.signal

from opendrop.geometry import Rect2

from .types import NeedleParam
from .hough import hough


_rng = np.random.default_rng()


def needle_guess(data: np.ndarray) -> Sequence[float]:
    params = np.empty(len(NeedleParam))
    data = data.astype(float)

    if data.shape[1] > 200:
        data = _rng.choice(data, size=100, replace=False, axis=1)

    extents = Rect2(data.min(axis=1), data.max(axis=1))
    diagonal = int(math.ceil((extents.w**2 + extents.h**2)**0.5))
    data -= np.reshape(extents.center, (2, 1))
    votes = hough(data, diagonal)

    needles = np.zeros(shape=(votes.shape[0], 3))
    for i in range(votes.shape[0]):
        peaks, props = scipy.signal.find_peaks(votes[i], prominence=0)
        if len(peaks) < 2: continue
        ix = np.argsort(props['prominences'])[::-1]
        peak1_i, peak2_i = peaks[ix[:2]]
        prom1, prom2 = props['prominences'][ix[:2]]
        if prom2 < prom1/2: continue

        peak1 = ((peak1_i - 1)/(len(votes[i]) - 3) - 0.5) * diagonal
        peak2 = ((peak2_i - 1)/(len(votes[i]) - 3) - 0.5) * diagonal

        needles[i][0] = (peak1 + peak2)/2
        needles[i][1] = math.fabs(peak1 - peak2)/2
        needles[i][2] = prom1 + prom2

    scores = scipy.ndimage.gaussian_filter(needles[:, 2], sigma=10, mode='wrap')
    needle_i = scores.argmax()
    
    theta = (needle_i/len(needles)) * np.pi + np.pi/2
    rho, radius = needles[needle_i][:2]

    rho_offset = np.cos(theta)*extents.xc - np.sin(theta)*extents.yc
    rho += rho_offset

    params[NeedleParam.ROTATION] = theta
    params[NeedleParam.RHO] = rho
    params[NeedleParam.RADIUS] = radius

    return params
