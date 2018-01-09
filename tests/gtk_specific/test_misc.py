import os

import cv2
import gi

gi.require_version('GdkPixbuf', '2.0')

from gi.repository import GdkPixbuf

from opendrop.gtk_specific.misc import pixbuf_from_array
from tests import samples

SAMPLES_DIR = os.path.dirname(samples.__file__)

TEST_IMAGE_PATH = os.path.join(SAMPLES_DIR, 'images', 'image0.png')


def test_pixbuf_from_array():
    im = cv2.imread(TEST_IMAGE_PATH)

    pixbuf = pixbuf_from_array(im)

    assert isinstance(pixbuf, GdkPixbuf.Pixbuf)

    assert im.tobytes() == pixbuf.get_pixels()
