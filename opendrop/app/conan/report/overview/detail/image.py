# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


import math
from typing import Optional

from gi.repository import Gtk, GObject

from opendrop.appfw import Presenter, component, install
from opendrop.geometry import Rect2, Vector2
from opendrop.widgets.canvas import Canvas, CanvasAlign, ImageArtist, LineArtist, AngleLabelArtist

from opendrop.app.conan.services.analysis import ConanAnalysisJob


@component(
    template_path='./image.ui',
)
class ConanReportOverviewImagePresenter(Presenter[Gtk.Container]):
    _analysis: Optional[ConanAnalysisJob] = None

    def after_view_init(self) -> None:
        self.canvas = Canvas(align=CanvasAlign.FIT, hexpand=True, vexpand=True, visible=True)
        self.host.add(self.canvas)

        self.bg_artist = ImageArtist()
        self.canvas.add_artist(self.bg_artist)

        self.baseline_artist = LineArtist(
            stroke_color=(0.25, 1.0, 0.25),
            scale_strokes=True,
        )
        self.canvas.add_artist(self.baseline_artist)

        self.left_angle_artist = AngleLabelArtist(
            clockwise=False,
            arc_radius=20.0,
            text_radius=40.0,
            end_line_radius=50.0,
            stroke_color=(1.0, 0.0, 0.5),
            text_color=(1.0, 0.0, 0.5),
            scale_radii=True,
            scale_strokes=True,
            scale_text=True,
        )
        self.canvas.add_artist(self.left_angle_artist)

        self.right_angle_artist = AngleLabelArtist(
            clockwise=True,
            arc_radius=20.0,
            text_radius=40.0,
            end_line_radius=50.0,
            stroke_color=(1.0, 0.0, 0.5),
            text_color=(1.0, 0.0, 0.5),
            scale_radii=True,
            scale_strokes=True,
            scale_text=True,
        )
        self.canvas.add_artist(self.right_angle_artist)

        self.baseline_artist.bind_property(
            'line',
            self.left_angle_artist, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: -math.atan(line.gradient) if line is not None else 0,
        )

        self.baseline_artist.bind_property(
            'line',
            self.right_angle_artist, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: math.pi - (math.atan(line.gradient) if line is not None else 0),
        )

    @install
    @GObject.Property
    def analysis(self) -> Optional[ConanAnalysisJob]:
        return self._analysis

    @analysis.setter
    def analysis(self, analysis: Optional[ConanAnalysisJob]) -> None:
        if self.analysis is not None:
            self.analysis.disconnect(self.analysis_status_changed_id)

        self._analysis = analysis

        if analysis is None:
            return

        self.analysis_status_changed_id = analysis.connect('notify::status', self.analysis_status_changed)
        self.analysis_status_changed()

    def analysis_status_changed(self, *_) -> None:
        analysis = self._analysis
        if analysis is None: return

        image = analysis.image
        if image is not None:
            self.bg_artist.set_array(image)
            self.bg_artist.props.extents = Rect2(0, 0, image.shape[1], image.shape[0])
            self.canvas.set_content_size(image.shape[1], image.shape[0])
            self.canvas.zoom(0.0)
        else:
            self.bg_artist.clear_data()

        left_angle = analysis.left_angle
        left_contact = analysis.left_contact
        if left_angle is not None and left_contact is not None:
            self.left_angle_artist.props.delta_angle = left_angle
            self.left_angle_artist.props.x = left_contact.x
            self.left_angle_artist.props.y = left_contact.y
        else:
            self.left_angle_artist.props.delta_angle = math.nan

        right_angle = analysis.right_angle
        right_contact = analysis.right_contact
        if right_angle is not None and right_contact is not None:
            self.right_angle_artist.props.delta_angle = -right_angle
            self.right_angle_artist.props.x = right_contact.x
            self.right_angle_artist.props.y = right_contact.y
        else:
            self.right_angle_artist.props.delta_angle = math.nan

        line = analysis.baseline
        self.baseline_artist.props.line = line

    def destroy(self, *_) -> None:
        self.analysis = None
