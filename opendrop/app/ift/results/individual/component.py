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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from .detail import detail_cs
from .master import master_cs
from .model import IndividualModel

individual_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@individual_cs.view()
class IndividualView(View['IndividualPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)

        _, detail_area = self.new_component(
            detail_cs.factory(
                in_analysis=self.presenter.bn_selection,
            )
        )
        detail_area.show()
        self._widget.pack1(detail_area, resize=True, shrink=False)

        _, master_area = self.new_component(
            master_cs.factory(
                in_analyses=self.presenter.bn_analyses,
                bind_selection=self.presenter.bn_selection,
            )
        )
        master_area.show()
        self._widget.pack2(master_area, resize=True, shrink=False)

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@individual_cs.presenter(options=['model'])
class IndividualPresenter(Presenter['IndividualView']):
    def _do_init(self, model: IndividualModel) -> None:
        self._model = model
        self.bn_analyses = model.bn_analyses
        self.bn_selection = model.bn_selection
