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
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Tuple, Optional

import cairo
import numpy as np
from gi.repository import GObject

from opendrop.utility.cairomisc import cairo_saved
from .. import abc


class MaskFill(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        mask = self._mask
        if mask is None:
            return

        scale = self._parent._widget_dist_from_canvas((1, 1))
        offset = self._parent._widget_coord_from_canvas((0, 0))

        with cairo_saved(cr):
            cr.translate(*offset)
            cr.scale(*scale)

            mask_width = mask.shape[1]
            mask_height = mask.shape[0]

            required_stride_len = cairo.Format.A8.stride_for_width(mask_width)
            required_padding = required_stride_len - mask_width

            if required_padding:
                mask = np.pad(mask, pad_width=((0, 0), (0, required_padding)), mode='constant', constant_values=0)

            mask_surface = cairo.ImageSurface.create_for_data(
                memoryview(mask),
                cairo.FORMAT_A8,
                mask_width,
                mask_height,
            )

            cr.set_source_rgba(*self._color)
            cr.mask_surface(mask_surface, 0, 0)

    _mask = None  # type: Optional[np.ndarray]

    @GObject.Property
    def mask(self) -> np.ndarray:
        return self._mask

    @mask.setter
    def mask(self, mask: np.ndarray) -> None:
        self._mask = mask
        self.emit('request-draw')

    _color = (0.0, 0.0, 0.0)

    @GObject.Property
    def color(self) -> Tuple[float, float, float]:
        return self._color

    @color.setter
    def color(self, color: Tuple[float, float, float]) -> None:
        self._color = color
        self.emit('request-draw')
