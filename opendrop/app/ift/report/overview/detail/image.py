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

import numpy as np

from gi.repository import Gtk, GObject

from opendrop.geometry import Rect2
from opendrop.appfw import Presenter, component, install
from opendrop.widgets.canvas import Canvas, CanvasAlign, ImageArtist, PolylineArtist
from opendrop.app.ift.services.analysis import PendantAnalysisJob


@component(
    template_path='./image.ui',
)
class IFTReportOverviewImagePresenter(Presenter[Gtk.Bin]):
    _analysis = None
    _event_connections = ()

    def __init__(self) -> None:
        self._canvas_cache = {}

    def after_view_init(self) -> None:
        self.canvas = Canvas(align=CanvasAlign.FIT, hexpand=True, vexpand=True, visible=True)
        self.host.add(self.canvas)

        self.image_artist = ImageArtist()
        self.canvas.add_artist(self.image_artist)

        self.drop_points_artist = ImageArtist()
        self.canvas.add_artist(self.drop_points_artist)

        self.drop_fit_artist = PolylineArtist(
            stroke_color=(1.0, 0.0, 0.5),
            scale_strokes=True,
        )
        self.canvas.add_artist(self.drop_fit_artist)

    @install
    @GObject.Property
    def analysis(self) -> Optional[PendantAnalysisJob]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[PendantAnalysisJob]) -> None:
        for conn in self._event_connections:
            conn.disconnect()
        self._event_connections = ()

        self._analysis = value

        if self._analysis is None:
            return

        self._event_connections = (
            self._analysis.bn_status.on_changed.connect(self.analysis_status_changed),
        )

        self.analysis_status_changed()

    def analysis_status_changed(self) -> None:
        if self._analysis is None: return

        status = self._analysis.bn_status.get()
        drop_region = self._analysis.bn_drop_region.get()

        if status is PendantAnalysisJob.Status.WAITING_FOR_IMAGE:
            self.image_artist.clear_data()
        else:
            image = self._analysis.bn_image.get()
            if drop_region is not None:
                image = image[drop_region.y0:drop_region.y1+1, drop_region.x0:drop_region.x1+1]
            self.image_artist.props.extents = Rect2(0, 0, image.shape[1], image.shape[0])
            self.image_artist.set_array(image)

            self.canvas.set_content_size(image.shape[1], image.shape[0])

        if status is PendantAnalysisJob.Status.WAITING_FOR_IMAGE \
                or status is PendantAnalysisJob.Status.EXTRACTING_FEATURES:
            self.drop_points_artist.clear_data()
        else:
            drop_points = self._analysis.bn_drop_profile_extract.get().copy()
            if drop_region is not None:
                drop_points -= drop_region.position
            data = np.zeros(image.shape[:2], np.uint32)
            data[tuple(drop_points.T)[::-1]] = 0xff8080ff
            self.drop_points_artist.props.extents = Rect2(0, 0, data.shape[1], data.shape[0])
            self.drop_points_artist.set_data(data, cairo.Format.ARGB32, data.shape[1], data.shape[0])

        if status is not PendantAnalysisJob.Status.FINISHED:
            self.drop_fit_artist.props.polyline = None
        else:
            fit = self._analysis.bn_drop_profile_fit.get().copy()
            if drop_region is not None:
                fit -= drop_region.position
            self.drop_fit_artist.props.polyline = fit

    def destroy(self, *_) -> None:
        self.analysis = None
