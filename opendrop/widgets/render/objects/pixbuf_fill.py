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


from typing import Optional

import cairo
from gi.repository import GObject, GdkPixbuf, Gdk

from opendrop.utility.cairomisc import cairo_saved
from .. import abc


class PixbufFill(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        pixbuf = self.props.pixbuf
        if pixbuf is None:
            return

        scale = self._parent._widget_dist_from_canvas((1, 1))
        offset = self._parent._widget_coord_from_canvas((0, 0))

        with cairo_saved(cr):
            cr.translate(*offset)
            cr.scale(*scale)

            Gdk.cairo_set_source_pixbuf(cr, pixbuf, pixbuf_x=0, pixbuf_y=0)
            cr.get_source().set_filter(cairo.Filter.FAST)
            cr.paint()

    _pixbuf = None  # type: Optional[GdkPixbuf.Pixbuf]

    @GObject.Property
    def pixbuf(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._pixbuf

    @pixbuf.setter
    def pixbuf(self, value: Optional[GdkPixbuf.Pixbuf]) -> None:
        self._pixbuf = value
        self.emit('request-draw')
