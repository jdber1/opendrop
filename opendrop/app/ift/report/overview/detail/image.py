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


from injector import inject
from opendrop.app.ift.services.edges import PendantEdgeDetectionParamsFactory
from typing import Optional

import cv2
import numpy as np

from gi.repository import Gtk, Gdk, GObject

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, component, install


@component(
    template_path='./image.ui',
)
class IFTReportOverviewImagePresenter(Presenter[Gtk.Bin]):
    _analysis = None
    _event_connections = ()

    @inject
    def __init__(self, *, edget_det_params: PendantEdgeDetectionParamsFactory) -> None:
        self._edge_det_params = edget_det_params
        self._canvas_cache = {}

    def after_view_init(self) -> None:
        from matplotlib.figure import Figure
        from matplotlib.image import AxesImage
        from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo

        figure = Figure(tight_layout=True)

        self.canvas = FigureCanvasGTK3Cairo(figure)
        self.canvas.show()

        self.host.add(self.canvas)

        self.canvas.connect('map', self.hdl_canvas_map)

        # Axes
        self.axes = figure.add_subplot(1, 1, 1)
        self.axes.set_aspect('equal', 'box')
        self.axes.xaxis.tick_top()
        for item in (*self.axes.get_xticklabels(), *self.axes.get_yticklabels()):
            item.set_fontsize(8)

        self.axes_image = AxesImage(ax=self.axes)

        # Placeholder transparent 1x1 image (rgba format)
        self.axes_image.set_data(np.zeros((1, 1, 4)))
        self.axes_image.set_extent((0, 1, 0, 1))
        self.axes.add_image(self.axes_image)

        self.profile_extract_line = self.axes.plot([], linestyle='-', color='#0080ff', linewidth=1.5)[0]
        self.profile_fit_line = self.axes.plot([], linestyle='-', color='#ff0080', linewidth=1)[0]

    def hdl_canvas_map(self, *_) -> None:
        self.canvas.draw_idle()

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
            self._analysis.bn_image.on_changed.connect(self.hdl_analysis_image_changed),
            self._analysis.bn_drop_profile_extract.on_changed.connect(self.hdl_analysis_drop_profile_fit_extract_changed),
            self._analysis.bn_drop_profile_fit.on_changed.connect(self.hdl_analysis_drop_profile_fit_changed),
        )

        self.hdl_analysis_image_changed()
        self.hdl_analysis_drop_profile_fit_extract_changed()
        self.hdl_analysis_drop_profile_fit_changed()

    def hdl_analysis_image_changed(self) -> None:
        if self._analysis is None: return

        image = self._analysis.bn_image.get()

        if image is None:
            self.axes.set_axis_off()
            self.axes_image.set_data(np.zeros((1, 1, 4)))
            self.axes_image.set_extent((0, 1, 0, 1))
            self.canvas.draw_idle()
            return

        drop_region = self._edge_det_params.drop_region
        assert drop_region is not None

        image = image[drop_region.y0:drop_region.y1, drop_region.x0:drop_region.x1]

        self.axes.set_axis_on()

        # Use a scaled down image so it draws faster.
        thumb_size = (min(400, image.shape[1]), min(400, image.shape[0]))
        image_thumb = cv2.resize(image, dsize=thumb_size)
        self.axes_image.set_data(image_thumb)

        self.axes_image.set_extent((0, image.shape[1], image.shape[0], 0))
        self.canvas.draw_idle()

    def hdl_analysis_drop_profile_fit_extract_changed(self) -> None:
        if self._analysis is None: return

        profile = self._analysis.bn_drop_profile_extract.get()

        if profile is None:
            self.profile_fit_line.set_visible(False)
            self.canvas.draw_idle()
            return

        drop_region = self._edge_det_params.drop_region
        assert drop_region is not None

        profile = profile - drop_region.position

        self.profile_fit_line.set_data(profile.T)
        self.profile_fit_line.set_visible(True)
        self.canvas.draw_idle()

    def hdl_analysis_drop_profile_fit_changed(self) -> None:
        if self._analysis is None: return

        profile = self._analysis.bn_drop_profile_fit.get()

        if profile is None:
            self.profile_extract_line.set_visible(False)
            self.canvas.draw_idle()
            return

        drop_region = self._edge_det_params.drop_region
        assert drop_region is not None

        profile = profile - drop_region.position

        self.profile_extract_line.set_data(profile.T)
        self.profile_extract_line.set_visible(True)
        self.canvas.draw_idle()

    def destroy(self, *_) -> None:
        self.analysis = None
