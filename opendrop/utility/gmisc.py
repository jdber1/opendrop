# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
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
