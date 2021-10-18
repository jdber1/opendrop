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


from typing import Iterable, Sequence

from gi.repository import Gtk, GObject

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, TemplateChild, component, install


@component(
    template_path='./report.ui',
)
class IFTReportPresenter(Presenter):
    #  frame = TemplateChild('frame')  # type: TemplateChild[Gtk.Frame]
    stack = TemplateChild('stack')  # type: TemplateChild[Gtk.Stack]
    stack_switcher = TemplateChild('stack_switcher')  # type: TemplateChild[Gtk.StackSwitcher]
    overview = TemplateChild('overview')

    _analyses = ()

    view_ready = False

    def after_view_init(self) -> None:
        self.view_ready = True
        self.update_graphs_visibility()

    @install
    @GObject.Property
    def analyses(self) -> Sequence[PendantAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[PendantAnalysisJob]) -> None:
        self._analyses = tuple(analyses)
        self.update_graphs_visibility()

    def update_graphs_visibility(self) -> None:
        if not self.view_ready: return

        if len(self._analyses) <= 1:
            self.hide_graphs()
        else:
            self.show_graphs()

    def show_graphs(self) -> None:
        self.stack_switcher.show()
        #  self.frame.set_shadow_type(Gtk.ShadowType.IN)

    def hide_graphs(self) -> None:
        self.stack_switcher.hide()
        self.stack.set_visible_child(self.overview)
        #  self.frame.set_shadow_type(Gtk.ShadowType.NONE)
