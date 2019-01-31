from typing import Sequence

import numpy as np
from gi.repository import GdkPixbuf, GLib


def pixbuf_from_array(image: Sequence[Sequence[Sequence[int]]]) -> GdkPixbuf.Pixbuf:
    if not isinstance(image, np.ndarray):
        image = np.array(image)

    # Assert that `image` has three or four channels
    assert len(image.shape) == 3 and (image.shape[-1] in (3, 4))

    # "Image data in 8-bit/sample packed format inside a `Glib.Bytes`"
    data = GLib.Bytes(image.astype(np.uint8).tobytes())  # type: bytes

    # Colour space of image, only RGB supported currently
    colorspace = GdkPixbuf.Colorspace.RGB  # type: GdkPixbuf.Colorspace

    # If the data has an opacity channel ?
    has_alpha = (image.shape[-1] == 4)  # type: bool

    # The size in bits of each R, G, B component?
    bits_per_sample = 8  # type: int

    # Width of the image
    width = image.shape[1]  # type: int

    # Height of the image
    height = image.shape[0]  # type: int

    # Basically the size of each row in bytes
    rowstride = image.strides[0]  # type: int

    pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
        data,
        colorspace,
        has_alpha,
        bits_per_sample,
        width,
        height,
        rowstride)

    return pixbuf
