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


from typing import Mapping, Any

from gi.repository import Gtk

from opendrop.app.common.sidebar import sidebar_cs
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.mvp.gtk import stack_cs
from opendrop.mvp.typing import ComponentFactory
from .model import WizardModel, WizardPageControls

wizard_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@wizard_cs.view(options=['titles', 'pages'])
class WizardView(View['WizardPresenter', Gtk.Grid]):
    def _do_init(self, titles: Mapping[Any, str], pages: Mapping[Any, ComponentFactory[Gtk.Widget]]) -> Gtk.Grid:
        self._widget = Gtk.Grid()

        # Sidebar
        _, sidebar_area = self.new_component(
            sidebar_cs.factory(
                active_title=self.presenter.current_page,
                titles=titles,
            )
        )
        sidebar_area.show()
        self._widget.attach(sidebar_area, 0, 0, 1, 1)

        # Footer container
        self._footer_area = Gtk.Grid()
        self._footer_area.show()
        self._widget.attach(self._footer_area, 0, 2, 2, 1)

        # Main content container
        _, pages_area = self.new_component(
            stack_cs.factory(
                active_stack=self.presenter.current_page,
                children={
                    page_id:
                        page_cf.fork(
                            footer_area=self._footer_area,
                            page_controls=WizardPageControls(
                                do_next_page=self.presenter.next_page,
                                do_prev_page=self.presenter.prev_page,
                            )
                        )
                    for page_id, page_cf in pages.items()
                },
                gtk_properties={'hexpand': True, 'vexpand': True},
            )
        )
        pages_area.show()
        self._widget.attach(pages_area, 1, 0, 1, 1)

        # Main content and Footer separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.show()
        self._widget.attach(separator, 0, 1, 2, 1)

        self._widget.show()

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@wizard_cs.presenter(options=['controller'])
class WizardPresenter(Presenter['WizardView']):
    def _do_init(self, controller: 'WizardModel') -> None:
        self._controller = controller
        self.current_page = controller.bn_current_page

    def next_page(self) -> None:
        self._controller.next_page()

    def prev_page(self) -> None:
        self._controller.prev_page()
