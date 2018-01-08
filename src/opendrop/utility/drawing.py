from typing import Sequence

import numpy as np
from gi.repository import GdkPixbuf, GLib


def pixbuf_from_array(image: Sequence[Sequence[Sequence[int]]]):
    if not isinstance(image, np.ndarray):
        image = np.array(image)

    # "Image data in 8-bit/sample packed format inside a `Glib.Bytes`"
    data = image.astype(np.uint8).tobytes()  # type: bytes

    # Colour space of image, only RGB supported currently
    colorspace = GdkPixbuf.Colorspace.RGB  # type: GdkPixbuf.Colorspace

    # If the data has an opacity channel ?
    has_alpha = False  # type: boolean

    # The size in bits of each R, G, B component?
    bits_per_sample = 8  # type: int

    # Width of the image
    width = image.shape[1]  # type: int

    # Height of the image
    height = image.shape[0]  # type: int

    # Basically the size of each row in bytes
    rowstride = width * bits_per_sample/8 * 3  # type: int

    pixbuf = GdkPixbuf.Pixbuf.new_from_data(
        data,
        colorspace,
        has_alpha,
        bits_per_sample,
        width,
        height,
        rowstride
    )  # type: GdkPixbuf.Pixbuf

    # Keep a reference to data otherwise it will be garbage collected
    pixbuf.data = data

    return pixbuf
