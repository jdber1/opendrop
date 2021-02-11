from typing import Optional

import cv2
import numpy as np

from opendrop.geometry import Line2, Rect2


__all__ = ('label_pendant_edges',)


def label_pendant_edges(
        image,
        baseline: Line2,
        *,
        thresh1: float = 100.0,
        thresh2: float = 200.0,
        dilate: int = 2,
        roi: Optional[Rect2[int]] = None,
):
    labels = np.zeros(shape=image.shape[:2], dtype=np.int32)
    
    if roi is None:
        roi = Rect2(0, 0, image.shape[1], image.shape[0])
    
    baseline = Line2(baseline.pt0 - roi.pt0, baseline.pt1 - roi.pt0)
    subimage = image[roi.y0:roi.y1+1, roi.x0:roi.x1+1]

    baseline_dir = baseline.pt1 - baseline.pt0
    perp = np.array([-baseline_dir.y, baseline_dir.x], dtype=float)
    perp /= np.linalg.norm(perp)

    edges = cv2.Canny(subimage, thresh1, thresh2)

    if dilate >= 2:
        fat_edges = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (dilate, dilate)))
    else:
        fat_edges = edges

    # Values returned are n_labels, labels, stats, centroids.
    _, fat_labels, fat_stats, _ = \
        cv2.connectedComponentsWithStats(fat_edges, connectivity=8)
    
    # Pick component with largest bounding box area as the pendant mask.
    ix = np.argsort(fat_stats[:, cv2.CC_STAT_AREA])[::-1]
    if ix[0] == 0:
        # Label 0 is the background.
        pendant_fat_label = ix[1]
    else:
        pendant_fat_label = ix[0]

    pendant_points = np.array((edges & fat_labels == pendant_fat_label).nonzero()[::-1])

    z = perp @ (pendant_points.T - baseline.pt0).T

    # Ignore points within ~ 4 pixels of the baseline.
    drop_points = pendant_points[:, z > 4]
    needle_points = pendant_points[:, z < -4]

    _, drop_rect_size, _ = cv2.minAreaRect(drop_points.T)
    _, needle_rect_size, _ = cv2.minAreaRect(needle_points.T)
    if min(needle_rect_size) > min(drop_rect_size):
        needle_points, drop_points = drop_points, needle_points
        
    edge_points = edges.nonzero()[::-1]
        
    labels[roi.y0 + edge_points[1], roi.x0 + edge_points[0]] = 1
    labels[roi.y0 + drop_points[1], roi.x0 + drop_points[0]] = 2
    labels[roi.y0 + needle_points[1], roi.x0 + needle_points[0]] = 3
    
    return labels
