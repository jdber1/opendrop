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


from gi.repository import Gtk
from injector import inject

from opendrop.app.ift.services.report import IFTReportService
from opendrop.appfw import Presenter, TemplateChild, ComponentFactory, component


@component(
    template_path='./report.ui',
)
class IFTReportPresenter(Presenter):
    frame = TemplateChild('frame')  # type: TemplateChild[Gtk.Frame]
    stack = TemplateChild('stack')  # type: TemplateChild[Gtk.Stack]
    stack_switcher = TemplateChild('stack_switcher')  # type: TemplateChild[Gtk.StackSwitcher]

    @inject
    def __init__(self, cf: ComponentFactory, report: IFTReportService) -> None:
        self.cf = cf
        self.report = report

    def after_view_init(self) -> None:
        self.overview = self.cf.create('IFTReportOverview', visible=True)
        self.stack.add_titled(self.overview, name='Individual Fit', title='Individual Fit')

        graphs = self.cf.create('IFTReportGraphs', visible=True)
        self.stack.add_titled(graphs, name='Graphs', title='Graphs')

        self.stack.props.visible_child = self.overview

        conn = self.report.bn_analyses.on_changed.connect(self.hdl_report_analyses_changed)
        self.host.connect('destroy', lambda *_: conn.disconnect())

        self.hdl_report_analyses_changed()

    def hdl_report_analyses_changed(self) -> None:
        analyses = self.report.bn_analyses.get()
        if len(analyses) <= 1:
            self.hide_graphs()
        else:
            self.show_graphs()

    def show_graphs(self) -> None:
        self.stack_switcher.show()
        self.frame.set_shadow_type(Gtk.ShadowType.IN)

    def hide_graphs(self) -> None:
        self.stack_switcher.hide()
        self.stack.set_visible_child(self.overview)
        self.frame.set_shadow_type(Gtk.ShadowType.NONE)
