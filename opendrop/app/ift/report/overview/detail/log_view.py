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


from gi.repository import Gtk, GObject
from typing import Optional

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import componentclass, TemplateChild


@componentclass(
    template_path='./log_view.ui',
)
class IFTReportOverviewLogView(Gtk.ScrolledWindow):
    __gtype_name__ = 'IFTReportOverviewLogView'

    _event_connections = ()
    _text_buffer = TemplateChild('text_buffer')

    _analysis = None
    _template_ready = False

    def after_template_init(self) -> None:
        self._template_ready = True
        # Update log.
        self._hdl_analysis_log_changed()

    @GObject.Property
    def analysis(self) -> Optional[IFTDropAnalysis]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[IFTDropAnalysis]) -> None:
        for conn in self._event_connections:
            conn.disconnect()
        self._event_connections = ()

        self._analysis = value

        if self._analysis is None:
            return

        self._event_connections = (
            self._analysis.bn_log.on_changed.connect(self._hdl_analysis_log_changed),
        )

        self._hdl_analysis_log_changed()

    def _hdl_analysis_log_changed(self) -> None:
        if not self._template_ready: return
        if self._analysis is None: return
        text = self._analysis.bn_log.get()
        self._text_buffer.set_text(text)

    def do_destroy(self) -> None:
        self._analysis = None
        Gtk.ScrolledWindow.do_destroy.invoke(Gtk.ScrolledWindow, self)
