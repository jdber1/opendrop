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

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import Inject, Injector, TemplateChild, componentclass

from .image import IFTReportOverviewImage
from .log_view import IFTReportOverviewLogView
from .parameters import IFTReportOverviewParameters
from .residuals import IFTReportOverviewResiduals


@componentclass(
    template_path='./detail.ui',
)
class IFTReportOverviewDetail(Gtk.Stack):
    __gtype_name__ = 'IFTReportOverviewDetail'

    _no_data_label = TemplateChild('no_data_label')
    _content = TemplateChild('content')
    _notebook = TemplateChild('notebook')

    _injector = Inject(Injector)

    _analysis = None
    _event_connections = ()
    _template_ready = False

    def after_template_init(self) -> None:
        parameters = self._injector.create_object(IFTReportOverviewParameters)
        self._content.attach(parameters, 0, 0, 1, 1)

        image = self._injector.create_object(IFTReportOverviewImage)
        image.show()
        self._notebook.append_page(image, Gtk.Label('Drop profile'))

        residuals = self._injector.create_object(IFTReportOverviewResiduals)
        residuals.show()
        self._notebook.append_page(residuals, Gtk.Label('Fit residuals'))

        log_view = self._injector.create_object(IFTReportOverviewLogView)
        log_view.show()
        self._notebook.append_page(log_view, Gtk.Label('Log'))

        self.bind_property('analysis', parameters, 'analysis', GObject.BindingFlags.SYNC_CREATE)
        self.bind_property('analysis', image, 'analysis', GObject.BindingFlags.SYNC_CREATE)
        self.bind_property('analysis', residuals, 'analysis', GObject.BindingFlags.SYNC_CREATE)
        self.bind_property('analysis', log_view, 'analysis', GObject.BindingFlags.SYNC_CREATE)

        self._template_ready = True

        # Invoke setter.
        self.analysis = self.analysis

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
            self.show_waiting_placeholder()
            return

        self._event_connections = (
            self._analysis.bn_image.on_changed.connect(self._hdl_analysis_image_changed),
        )

        self._hdl_analysis_image_changed()

    def _hdl_analysis_image_changed(self) -> None:
        if self._analysis is None or self._analysis.bn_image.get() is None:
            self.show_waiting_placeholder()
        else:
            self.hide_waiting_placeholder()

    def show_waiting_placeholder(self) -> None:
        if not self._template_ready:
            return
        self.set_visible_child(self._no_data_label)

    def hide_waiting_placeholder(self) -> None:
        if not self._template_ready:
            return
        self.set_visible_child(self._content)

    def do_destroy(self) -> None:
        self.analysis = None
        Gtk.Stack.do_destroy.invoke(Gtk.Stack, self)
