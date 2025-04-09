from typing import NamedTuple, Optional, Any

import cv2
import numpy as np

from opendrop.geometry import Line2, Rect2


__all__ = ('ContactAngleFeatures', 'extract_contact_angle_features')


class ContactAngleFeatures(NamedTuple):
    labels: np.ndarray
    drop_points: np.ndarray = np.empty((2, 0), dtype=int)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ContactAngleFeatures):
            return False

        for v1, v2 in zip(self, other):
            if isinstance(v1, np.ndarray):
                if not np.all(v1 == v2): return False
            else:
                if not (v1 == v2): return False

        return True


def extract_contact_angle_features(
        image,
        baseline: Optional[Line2],
        inverted: bool,
        *,
        roi: Optional[Rect2[int]] = None,
        thresh: float = 0.5,
        labels: bool = False,
) -> ContactAngleFeatures:
    if roi is None:
        roi = Rect2(0, 0, image.shape[1] - 1, image.shape[0] - 1)

    # Clip roi to within image extents.
    roi = Rect2(
        max(0, roi.x0),
        max(0, roi.y0),
        min(image.shape[1], roi.x1),
        min(image.shape[0], roi.y1),
    )

    subimage = image[roi.y0:roi.y1+1, roi.x0:roi.x1+1]
    if baseline is not None:
        baseline -= roi.position

        if baseline.pt1.x < baseline.pt0.x:
            baseline = Line2(baseline.pt1, baseline.pt0)

        if inverted:
            up = baseline.perp
            right = baseline.unit
            origin = np.array(baseline.pt0)
        else:
            # Origin is at the top in image coordinates, we want to analyse the drop with the origin at the
            # bottom since it's easier to reason with.
            up = -baseline.perp
            right = baseline.unit
            origin = np.array(baseline.pt0)

    if len(subimage.shape) > 2:
        subimage = cv2.cvtColor(subimage, cv2.COLOR_RGB2GRAY)

    blur = cv2.GaussianBlur(subimage, ksize=(5, 5), sigmaX=0)
    dx = cv2.Scharr(blur, cv2.CV_16S, dx=1, dy=0)
    dy = cv2.Scharr(blur, cv2.CV_16S, dx=0, dy=1)

    # Use magnitude of gradient squared to get sharper edges.
    mask = (dx.astype(float)**2 + dy.astype(float)**2)
    mask = np.sqrt(mask)
    mask = (mask/mask.max() * (2**8 - 1)).astype(np.uint8)

    # Ignore weak gradients.
    mask[mask < thresh * mask.max()] = 0

    cv2.adaptiveThreshold(
        mask,
        maxValue=1,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=5,
        C=0,
        dst=mask
    )

    if labels:
        # Hack: Thin edges using cv2.Canny()
        grad_max = (abs(dx) + abs(dy)).max()
        edges = cv2.Canny(mask*dx, mask*dy, grad_max*thresh/2, grad_max*thresh)
        edge_points = np.array(edges.nonzero()[::-1])
    else:
        edges = None
        edge_points = np.empty((2, 0), dtype=int)

    if baseline is not None:
        mask_ij = np.array(mask.nonzero())
        y = up @ (mask_ij[::-1] - origin.reshape(2, 1))

        ix = y.argsort()
        mask_ij = mask_ij[:, ix]
        y = y[ix]

        # Ignore edges below and within 2 pixels of the baseline.
        stop = np.searchsorted(y, 2.0, side='right')
        mask[tuple(mask_ij[:, :stop])] = 0

        # Use the two (needle separates drop edge into two) largest edges in the image.
        _, cc_labels, cc_stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
        ix = np.argsort(cc_stats[:, cv2.CC_STAT_WIDTH] * cc_stats[:, cv2.CC_STAT_HEIGHT])[::-1]
        ix = ix[:3]
        # Label 0 is the background.
        ix = ix[ix != 0]

        if len(ix) >= 2:
            cc_extents0 = Rect2(
                x=cc_stats[ix[0], cv2.CC_STAT_LEFT],
                y=cc_stats[ix[0], cv2.CC_STAT_TOP],
                w=cc_stats[ix[0], cv2.CC_STAT_WIDTH],
                h=cc_stats[ix[0], cv2.CC_STAT_HEIGHT],
            )
            cc_extents1 = Rect2(
                x=cc_stats[ix[1], cv2.CC_STAT_LEFT],
                y=cc_stats[ix[1], cv2.CC_STAT_TOP],
                w=cc_stats[ix[1], cv2.CC_STAT_WIDTH],
                h=cc_stats[ix[1], cv2.CC_STAT_HEIGHT],
            )

            # If one of the connected components is contained within the other, then just use the outer one.
            # Or if one component is much larger than the other.
            if cc_extents1.x0 > cc_extents0.x0 \
                    and cc_extents1.y0 > cc_extents0.y0 \
                    and cc_extents1.x1 < cc_extents0.x1 \
                    and cc_extents1.y1 < cc_extents0.y1 \
                    or cc_extents0.w*cc_extents0.h > 10*cc_extents1.w*cc_extents1.h:
                mask &= cc_labels == ix[0]
            else:
                mask &= (cc_labels == ix[0]) | (cc_labels == ix[1])
        elif len(ix) == 1:
            mask &= cc_labels == ix[0]

        # Hack: Thin edges using cv2.Canny()
        if edges is None:
            grad_max = (abs(dx) + abs(dy)).max()
            drop_edges = cv2.Canny(mask*dx, mask*dy, grad_max*thresh/2, grad_max*thresh)
        else:
            drop_edges = edges & mask

        drop_points = np.array(drop_edges.nonzero()[::-1])

        if drop_points.shape[1] > 0:
            mask = np.zeros(drop_points.shape[1], dtype=bool)

            x, y = [up, right] @ (drop_points - origin.reshape(2, 1))
            
            # Sort in ascending y coordinate.
            ix = y.argsort()
            x, y = x[ix], y[ix]
            drop_points = drop_points[:, ix]

            # Divide into 2 pixel high level sets.
            levels = np.histogram_bin_edges(y, bins=max(1, int(y.max()/2)))
            levels_ix = (0, *np.searchsorted(y, levels[1:], side='right'))

            # Find left and right-most edges in pairs of level sets.
            for start, stop in zip(levels_ix, levels_ix[min(2, len(levels_ix)-1):]):
                level_set = x[start:stop]

                # Left-to-right index.
                ltr_ix = level_set.argsort()

                # Split into clusters where x distances are less than 2*sqrt(2) ~ 2.828.
                # We use 2*sqrt(2) instead of sqrt(2) to allow for single pixel gaps.
                contiguous_groups = np.split(
                    ltr_ix,
                    #  (np.diff(level_set[ltr_ix]) > 2.828).nonzero()[0] + 1,
                    (np.diff(level_set[ltr_ix]) > 2.828).nonzero()[0] + 1,
                )
                mask[start + contiguous_groups[0]] = True
                mask[start + contiguous_groups[-1]] = True

            drop_points = drop_points[:, mask]
    else:
        drop_points = np.empty((2, 0), dtype=int)

    edge_points = edge_points + np.reshape(roi.position, (2, 1))
    drop_points = drop_points + np.reshape(roi.position, (2, 1))

    if labels:
        labels_array = np.zeros(image.shape[:2], np.uint8)
        labels_array[tuple(edge_points)[::-1]] = 1
        labels_array[tuple(drop_points)[::-1]] = 2
    else:
        labels_array = None


    return ContactAngleFeatures(
        labels=labels_array,
        drop_points=drop_points,
    )
