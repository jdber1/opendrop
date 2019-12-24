import ctypes
from typing import Sequence

import numpy as np
from gi.repository import GdkPixbuf
from numpy.lib import stride_tricks


def pixbuf_from_array(image: Sequence[Sequence[Sequence[int]]]) -> GdkPixbuf.Pixbuf:
    if not isinstance(image, np.ndarray):
        image = np.array(image)

    # Assert that `image` has three or four channels
    assert len(image.shape) == 3 and (image.shape[-1] in (3, 4))

    # Colour space of image, only RGB supported currently
    colorspace = GdkPixbuf.Colorspace.RGB  # type: GdkPixbuf.Colorspace

    # If the data has an opacity channel
    has_alpha = (image.shape[-1] == 4)  # type: bool

    # The size in bits of each R, G, B component
    bits_per_sample = 8  # type: int

    # Width of the image
    width = image.shape[1]  # type: int

    # Height of the image
    height = image.shape[0]  # type: int

    pixbuf = GdkPixbuf.Pixbuf.new(
        colorspace=colorspace,
        has_alpha=has_alpha,
        bits_per_sample=bits_per_sample,
        width=width,
        height=height,
    )

    pixbuf_pixels_pointer = ctypes.cast(pixbuf.props.pixels, ctypes.POINTER(ctypes.c_uint8))

    pixbuf_pixels_array = stride_tricks.as_strided(
        np.ctypeslib.as_array(
            pixbuf_pixels_pointer,
            shape=image.shape,
        ),
        strides=(pixbuf.props.rowstride, pixbuf.props.n_channels, 1)
    )

    np.copyto(dst=pixbuf_pixels_array, src=image)

    return pixbuf
