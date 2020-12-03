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

from gi.repository import GObject, Gtk

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, TemplateChild, component, install


@component(
    template_path='./detail.ui',
)
class IFTReportOverviewDetailPresenter(Presenter[Gtk.Stack]):
    no_data_label = TemplateChild('no_data_label')
    content = TemplateChild('content')

    _analysis = None
    event_connections = ()

    view_ready = False

    def after_view_init(self) -> None:
        self.view_ready = True
        # Invoke setter.
        self.analysis = self.analysis

    @install
    @GObject.Property
    def analysis(self) -> Optional[PendantAnalysisJob]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[PendantAnalysisJob]) -> None:
        for conn in self.event_connections:
            conn.disconnect()
        self.event_connections = ()

        self._analysis = value

        if self._analysis is None:
            self.show_waiting_placeholder()
            return

        self.event_connections = (
            self._analysis.bn_image.on_changed.connect(self.hdl_analysis_image_changed),
        )

        self.hdl_analysis_image_changed()

    def hdl_analysis_image_changed(self) -> None:
        if self._analysis is None or self._analysis.bn_image.get() is None:
            self.show_waiting_placeholder()
        else:
            self.hide_waiting_placeholder()

    def show_waiting_placeholder(self) -> None:
        if not self.view_ready:
            return
        self.host.set_visible_child(self.no_data_label)

    def hide_waiting_placeholder(self) -> None:
        if not self.view_ready:
            return
        self.host.set_visible_child(self.content)

    def destroy(self, *_) -> None:
        self.analysis = None
