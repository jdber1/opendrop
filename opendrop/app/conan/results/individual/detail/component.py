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
import math
from typing import Optional

from gi.repository import Gtk

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.geometry import Vector2
from .info import info_cs

detail_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@detail_cs.view()
class DetailView(View['DetailPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Stack(margin=10)

        self._body = Gtk.Grid(column_spacing=10)
        self._body.show()
        self._widget.add(self._body)

        _, info_area = self.new_component(
            info_cs.factory(
                in_image=self.presenter.bn_image,
                in_left_angle=self.presenter.bn_left_angle,
                in_left_point=self.presenter.bn_left_point,
                in_right_angle=self.presenter.bn_right_angle,
                in_right_point=self.presenter.bn_right_point,
                in_surface_line=self.presenter.bn_surface_line,
            )
        )
        info_area.show()
        self._body.attach(info_area, 0, 0, 1, 1)

        self._waiting_placeholder = Gtk.Label()
        self._waiting_placeholder.set_markup('<b>No data</b>')
        self._waiting_placeholder.show()
        self._widget.add(self._waiting_placeholder)

        self.presenter.view_ready()

        return self._widget

    def show_waiting_placeholder(self) -> None:
        self._widget.set_visible_child(self._waiting_placeholder)

    def hide_waiting_placeholder(self) -> None:
        self._widget.set_visible_child(self._body)

    def _do_destroy(self) -> None:
        self._widget.destroy()


@detail_cs.presenter(options=['in_analysis'])
class DetailPresenter(Presenter['DetailView']):
    def _do_init(
            self,
            in_analysis: Bindable[Optional[ConanAnalysis]]
    ) -> None:
        self._bn_analysis = in_analysis
        self._analysis_unbind_tasks = []

        self.bn_image = VariableBindable(None)

        self.bn_left_angle = VariableBindable(math.nan)
        self.bn_left_point = VariableBindable(Vector2(math.nan, math.nan))
        self.bn_right_angle = VariableBindable(math.nan)
        self.bn_right_point = VariableBindable(Vector2(math.nan, math.nan))

        self.bn_surface_line = VariableBindable(None)

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._bn_analysis.on_changed.connect(
                self._hdl_analysis_changed
            )
        ])

        self._hdl_analysis_changed()

    def _hdl_analysis_changed(self) -> None:
        self._unbind_analysis()

        analysis = self._bn_analysis.get()
        if analysis is None:
            self.view.show_waiting_placeholder()
            return

        self.view.hide_waiting_placeholder()

        self._bind_analysis(analysis)

    def _bind_analysis(self, analysis: ConanAnalysis) -> None:
        assert len(self._analysis_unbind_tasks) == 0

        data_bindings = [
            analysis.bn_image.bind_to(self.bn_image),
            analysis.bn_left_angle.bind_to(self.bn_left_angle),
            analysis.bn_left_point.bind_to(self.bn_left_point),
            analysis.bn_right_angle.bind_to(self.bn_right_angle),
            analysis.bn_right_point.bind_to(self.bn_right_point),
            analysis.bn_surface_line.bind_to(self.bn_surface_line),
        ]

        self._analysis_unbind_tasks.extend(
            db.unbind for db in data_bindings
        )

        event_connections = [
            analysis.bn_image.on_changed.connect(
                self._hdl_analysis_image_changed
            ),
        ]

        self._analysis_unbind_tasks.extend(
            ec.disconnect for ec in event_connections
        )

        self._hdl_analysis_image_changed()

    def _hdl_analysis_image_changed(self) -> None:
        analysis = self._bn_analysis.get()
        image = analysis.bn_image.get()
        if image is None:
            self.view.show_waiting_placeholder()
        else:
            self.view.hide_waiting_placeholder()

    def _unbind_analysis(self) -> None:
        for task in self._analysis_unbind_tasks:
            task()
        self._analysis_unbind_tasks.clear()

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        self._unbind_analysis()
