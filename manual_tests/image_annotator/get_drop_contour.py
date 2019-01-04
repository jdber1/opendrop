import colorsys
from pathlib import Path

import cv2
import numpy as np

from opendrop.app.ift.analysis_model.image_annotator.image_annotator import _get_drop_contour

IMAGE_FILE = Path(__file__).parent/'sample_drop_outline.png'


# Load image
drop_img = cv2.imread(str(IMAGE_FILE), cv2.IMREAD_GRAYSCALE)

# Call _get_drop_contour()
drop_contour = _get_drop_contour(drop_img)

# Visualizing contours
show_img = cv2.cvtColor(drop_img, cv2.COLOR_GRAY2RGB)

for i, p in enumerate(drop_contour):
    i_percentage = i / len(drop_contour)
    show_img[tuple(p[::-1])] = np.array(colorsys.hsv_to_rgb(i_percentage, 1, 1)[::-1]) * 255

show_img = cv2.cvtColor(show_img, cv2.COLOR_BGR2RGB)

# Show contours
cv2.imshow("Drop contour of '{!s}'".format(IMAGE_FILE), show_img)
cv2.waitKey(0)
