from typing import NamedTuple, Optional, Tuple
import math

import cv2
import numpy as np
import scipy.optimize

from opendrop.geometry import Rect2, Vector2
from opendrop.utility.misc import rotation_mat2d


__all__ = ('PendantFeatures', 'extract_pendant_features', 'find_pendant_apex')


# Math constants.
PI = math.pi

RotatedRect = Tuple[Vector2[float], Vector2[float], Vector2[float], Vector2[float]]


class PendantFeatures(NamedTuple):
    labels: np.ndarray

    drop_points: np.ndarray = np.empty((2, 0))

    drop_apex: Optional[Vector2[int]] = None
    drop_radius: Optional[float] = None
    drop_rotation: Optional[float] = None

    needle_rect: Optional[RotatedRect] = None
    needle_diameter: Optional[float] = None

    def __eq__(self, other: 'PendantFeatures') -> bool:
        if not isinstance(other, PendantFeatures):
            return False

        for v1, v2 in zip(self, other):
            if isinstance(v1, np.ndarray):
                if not (v1 == v2).all():
                    return False
            else:
                if not (v1 == v2):
                    return False
        else:
            return True


def extract_pendant_features(
        image,
        drop_region: Optional[Rect2[int]] = None,
        needle_region: Optional[Rect2[int]] = None,
        *,
        thresh1: float = 100.0,
        thresh2: float = 200.0,
        labels: bool = False,
) -> PendantFeatures:
    from opendrop.fit import needle_fit

    if drop_region is not None:
        drop_image = image[drop_region.y0:drop_region.y1+1, drop_region.x0:drop_region.x1+1]
    else:
        drop_image = None

    if needle_region is not None:
        needle_image = image[needle_region.y0:needle_region.y1+1, needle_region.x0:needle_region.x1+1]
    else:
        needle_image = None

    drop_points = np.empty((2, 0))
    drop_apex = None
    drop_radius = None
    drop_rotation = None

    if drop_image is not None:
        if len(drop_image.shape) > 2:
            drop_image = cv2.cvtColor(drop_image, cv2.COLOR_RGB2GRAY)

        drop_points = _extract_drop_edge(drop_image, thresh1, thresh2)

        # There shouldn't be more points than the perimeter of the image.
        if drop_points.shape[1] < 2*(image.shape[0] + image.shape[1]):
            ans = find_pendant_apex(drop_points)
            if ans is not None:
                drop_apex, drop_radius, drop_rotation = ans

    needle_points = np.empty((2, 0))
    needle_rect = None
    needle_diameter = None

    if needle_image is not None:
        needle_edges = cv2.Canny(needle_image, thresh1, thresh2)
        needle_points = np.array(needle_edges.nonzero()[::-1])

        # Use left and right-most points only for fitting.
        needle_outer_points = np.block([
            [np.argmax(needle_edges, axis=1),
             (needle_edges.shape[1] - 1) - np.argmax(needle_edges[:, ::-1], axis=1)],
            [np.arange(needle_edges.shape[0]),
             np.arange(needle_edges.shape[0])],
        ])

        needle_fit_result = needle_fit(needle_outer_points)
        if needle_fit_result is not None:
            needle_residuals = np.abs(needle_fit_result.residuals)
            needle_lmask = needle_fit_result.lmask
            needle_rmask = ~needle_lmask
            needle_lpoints = needle_outer_points[:, (needle_residuals < 1.0) & needle_lmask]
            needle_rpoints = needle_outer_points[:, (needle_residuals < 1.0) & needle_rmask]
            n_lpoints = needle_lpoints.shape[1]
            n_rpoints = needle_rpoints.shape[1]

            # Make sure there's an even number of points on the left and right sides, otherwise probably a bad
            # fit.
            if n_lpoints > 0 and n_rpoints > 0 and abs(n_lpoints - n_rpoints)/(n_lpoints + n_rpoints) < 0.33:
                needle_rho = needle_fit_result.rho
                needle_radius = needle_fit_result.radius
                needle_rotation = needle_fit_result.rotation

                needle_rotation_mat = rotation_mat2d(needle_rotation)
                needle_perp = needle_rotation_mat @ [1, 0]
                needle_lpoints_z = (needle_rotation_mat.T @ needle_lpoints)[1]
                needle_rpoints_z = (needle_rotation_mat.T @ needle_rpoints)[1]
                needle_min_z = min(needle_lpoints_z.min(), needle_rpoints_z.min())
                needle_max_z = max(needle_lpoints_z.max(), needle_rpoints_z.max())
                needle_tip1 = needle_rotation_mat @ [needle_rho, needle_min_z]
                needle_tip2 = needle_rotation_mat @ [needle_rho, needle_max_z]

                needle_rect = (
                    Vector2(needle_tip1 - needle_perp*needle_radius),
                    Vector2(needle_tip1 + needle_perp*needle_radius),
                    Vector2(needle_tip2 - needle_perp*needle_radius),
                    Vector2(needle_tip2 + needle_perp*needle_radius),
                )
                needle_diameter = 2 * needle_radius


    if drop_region is not None:
        drop_points += np.reshape(drop_region.position, (2, 1))
        if drop_apex is not None:
            drop_apex += drop_region.position

    if needle_region is not None:
        needle_points += np.reshape(needle_region.position, (2, 1))
        if needle_rect is not None:
            needle_rect = (
                needle_region.position + needle_rect[0],
                needle_region.position + needle_rect[1],
                needle_region.position + needle_rect[2],
                needle_region.position + needle_rect[3],
            )

    if labels:
        labels_array = np.zeros(image.shape[:2], dtype=np.uint8)
        labels_array[tuple(drop_points)[::-1]] = 1
        labels_array[tuple(needle_points)[::-1]] = 2
    else:
        labels_array = None

    return PendantFeatures(
        labels=labels_array,

        drop_points=drop_points,
        drop_apex=drop_apex,
        drop_radius=drop_radius,
        drop_rotation=drop_rotation,

        needle_rect = needle_rect,
        needle_diameter = needle_diameter,
    )


def _extract_drop_edge(gray: np.ndarray, thresh1: float, thresh2: float) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, ksize=(5, 5), sigmaX=0)
    dx = cv2.Scharr(blur, cv2.CV_32F, dx=1, dy=0)
    dy = cv2.Scharr(blur, cv2.CV_32F, dx=0, dy=1)

    # Use magnitude of gradient squared to get sharper edges.
    grad = dx**2 + dy**2
    grad /= grad.max()
    grad = (grad * (2**8 - 1)).astype(np.uint8)

    cv2.adaptiveThreshold(
        grad,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=5,
        C=0,
        dst=grad
    )

    # Hack: Use cv2.Canny() to do non-max suppression on grad.
    mask = _largest_connected_component(grad)
    edges = cv2.Canny(gray, thresh1, thresh2)
    edges *= mask
    points = np.array(edges.nonzero()[::-1])

    return points


def _largest_connected_component(gray: np.ndarray) -> np.ndarray:
    mask: np.ndarray

    # Values returned are n_labels, labels, stats, centroids.
    _, labels, stats, _ = cv2.connectedComponentsWithStats(gray, connectivity=4)
    
    ix = np.argsort(stats[:, cv2.CC_STAT_WIDTH] * stats[:, cv2.CC_STAT_HEIGHT])[::-1]
    if len(ix) > 1:
        if ix[0] == 0:
            # Label 0 is the background.
            biggest_label = ix[1]
        else:
            biggest_label = ix[0]

        mask = (labels == biggest_label)
    else:
        mask = np.ones(gray.shape, dtype=bool)
    
    return mask


def find_pendant_apex(data: Tuple[np.ndarray, np.ndarray]) -> Optional[tuple]:
    x, y = data

    if len(x) == 0 or len(y) == 0:
        return None

    xc = x.mean()
    yc = y.mean()
    radius = np.hypot(x - xc, y - yc).mean()

    # Fit a circle to the most circular part of the data.
    try:
        ans = scipy.optimize.least_squares(
            _circle_residues,
            (xc, yc, radius),
            _circle_jac,
            args=(x, y),
            loss='arctan',  # Ignore outliers.
            f_scale=radius/100,
            x_scale=(radius, radius, radius),
            max_nfev=50,
        )
    except ValueError:
        return None

    xc, yc, radius = ans.x
    resids = np.abs(ans.fun)
    resids_50ptile = np.quantile(resids, 0.5)

    # The somewhat circular-ish part of the drop profile.
    bowl_mask = resids < 10*resids_50ptile
    bowl_x = x[bowl_mask]
    bowl_y = y[bowl_mask]

    if len(bowl_x) == 0:
        return None

    # Don't need these variables anymore.
    del resids, resids_50ptile

    # Find the symmetry axis of bowl.
    Ixx, Iyy, Ixy = _calculate_inertia(bowl_x, bowl_y)

    # Eigenvector calculation for a symmetric 2x2 matrix.
    rotation = 0.5 * np.arctan2(2 * Ixy, Ixx - Iyy)
    unit_r = np.array([ np.cos(rotation), np.sin(rotation)])
    unit_z = np.array([-np.sin(rotation), np.cos(rotation)])

    bowl_r = unit_r @ [bowl_x - xc, bowl_y - yc]
    bowl_z = unit_z @ [bowl_x - xc, bowl_y - yc]
    bowl_r_ix = np.argsort(bowl_r)
    bowl_z_ix = np.argsort(bowl_z)

    # Calculate "asymmetry" along each axis. We define this to be the squared difference between the left and
    # right points, integrated along the axis.
    ma_kernel = np.ones(max(1, len(bowl_r)//10))
    ma_kernel /= len(ma_kernel)
    asymm_r = (np.convolve((bowl_z - bowl_z.mean())[bowl_r_ix], ma_kernel, mode='valid')**2).sum()
    asymm_z = (np.convolve((bowl_r - bowl_r.mean())[bowl_z_ix], ma_kernel, mode='valid')**2).sum()
    if asymm_z > asymm_r:
        # Swap axes so z is the symmetry axis.
        rotation -= PI/2
        unit_r, unit_z = -unit_z, unit_r
        bowl_r, bowl_z = -bowl_z, bowl_r
        bowl_r_ix, bowl_z_ix = bowl_z_ix[::-1], bowl_r_ix

    # No longer useful variables (and potentially incorrect after axes swapping).
    del asymm_r, asymm_z

    bowl_z_hist, _ = np.histogram(bowl_z, bins=2 + len(bowl_z)//10)
    if bowl_z_hist.argmax() > len(bowl_z_hist)/2:
        # Rotate by 180 degrees since points are accumulating (where dz/ds ~ 0) at high z, i.e. drop apex is
        # not on the bottom.
        rotation += PI
        unit_r *= -1
        unit_z *= -1
        bowl_r *= -1
        bowl_z *= -1
        bowl_r_ix = bowl_r_ix[::-1]
        bowl_z_ix = bowl_z_ix[::-1]

    bowl_z_ix_apex_arc_stop = np.searchsorted(np.abs(bowl_r), 0.3*radius, side='right', sorter=bowl_z_ix)
    apex_arc_ix = bowl_z_ix[:bowl_z_ix_apex_arc_stop]
    apex_arc_x = bowl_x[apex_arc_ix]
    apex_arc_y = bowl_y[apex_arc_ix]

    if len(apex_arc_ix) > 10:
        # Fit another circle to a smaller arc around the apex. Points within 0.3 radians of the apex should
        # have roughly constant curvature across typical Bond values.
        try:
            ans = scipy.optimize.least_squares(
                _circle_residues,
                (xc, yc, radius),
                _circle_jac,
                args=(apex_arc_x, apex_arc_y),
                method='lm',
                x_scale=(radius, radius, radius),
                max_nfev=50,
            )
        except ValueError:
            pass
        else:
            xc, yc, radius = ans.x 

    apex_x, apex_y = [xc, yc] - radius * unit_z

    # Restrict rotation to [-pi, pi].
    rotation = (rotation + PI) % (2*PI) - PI

    return Vector2(apex_x, apex_y), radius, rotation


def _calculate_inertia(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    x = x - x.mean()
    y = y - y.mean()
    
    Ixx = (y**2).sum()
    Iyy = (x**2).sum()
    Ixy = -(x @ y)
    
    return Ixx, Iyy, Ixy


def _circle_residues(params, x, y):
    xc, yc, radius = params
    r = np.hypot(x - xc, y - yc)
    return r - radius


def _circle_jac(params, x, y):
    jac = np.empty((len(x), 3))

    xc, yc, radius = params
    dist_x = x - xc
    dist_y = y - yc
    r = np.hypot(dist_x, dist_y)

    jac[:, 0] = -dist_x/r
    jac[:, 1] = -dist_y/r
    jac[:, 2] = -1

    return jac
