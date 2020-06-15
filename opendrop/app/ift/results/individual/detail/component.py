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


import math
from typing import Optional

from gi.repository import Gtk

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.app.ift.results.individual.detail.log_view import log_cs
from opendrop.app.ift.results.individual.detail.residuals import residuals_plot_cs
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable
from .parameters import parameters_cs
from .profile_fit import drop_fit_cs

detail_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@detail_cs.view()
class DetailView(View['DetailPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Stack(margin=10)

        self._body = Gtk.Grid(column_spacing=10)
        self._body.show()
        self._widget.add(self._body)

        _, parameters_area = self.new_component(
            parameters_cs.factory(
                in_interfacial_tension=self.presenter.bn_interfacial_tension,
                in_volume=self.presenter.bn_volume,
                in_surface_area=self.presenter.bn_surface_area,
                in_worthington=self.presenter.bn_worthington,
                in_bond_number=self.presenter.bn_bond_number,
                in_apex_coords=self.presenter.bn_apex_coords,
                in_image_angle=self.presenter.bn_image_angle,
            )
        )
        parameters_area.show()
        self._body.attach(parameters_area, 0, 0, 1, 1)

        notebook = Gtk.Notebook(hexpand=True, vexpand=True)
        notebook.show()
        self._body.attach(notebook, 1, 0, 1, 1)

        _, drop_fit_area = self.new_component(
            drop_fit_cs.factory(
                in_drop_image=self.presenter.bn_drop_image,
                in_drop_profile_extract=self.presenter.bn_drop_profile_extract,
                in_drop_profile_fit=self.presenter.bn_drop_profile_fit,
            )
        )
        drop_fit_area.show()
        notebook.append_page(drop_fit_area, Gtk.Label('Drop profile'))

        _, residuals_plot_area = self.new_component(
            residuals_plot_cs.factory(
                in_residuals=self.presenter.bn_residuals,
            )
        )
        residuals_plot_area.show()
        notebook.append_page(residuals_plot_area, Gtk.Label('Fit residuals'))

        _, log_area = self.new_component(
            log_cs.factory(
                in_log_text=self.presenter.bn_log_text,
            )
        )
        log_area.show()
        notebook.append_page(log_area, Gtk.Label('Log'))

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
            in_analysis: Bindable[Optional[IFTDropAnalysis]]
    ) -> None:
        self._bn_analysis = in_analysis
        self._analysis_unbind_tasks = []

        self.bn_interfacial_tension = VariableBindable(math.nan)
        self.bn_volume = VariableBindable(math.nan)
        self.bn_surface_area = VariableBindable(math.nan)
        self.bn_worthington = VariableBindable(math.nan)
        self.bn_bond_number = VariableBindable(math.nan)
        self.bn_apex_coords = VariableBindable((math.nan, math.nan))
        self.bn_image_angle = VariableBindable(math.nan)

        self.bn_drop_image = VariableBindable(None)
        self.bn_drop_profile_extract = VariableBindable(None)
        self.bn_drop_profile_fit = VariableBindable(None)

        self.bn_residuals = VariableBindable(None)

        self.bn_log_text = VariableBindable('')

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

    def _bind_analysis(self, analysis: IFTDropAnalysis) -> None:
        assert len(self._analysis_unbind_tasks) == 0

        data_bindings = [
            analysis.bn_interfacial_tension.bind_to(self.bn_interfacial_tension),
            analysis.bn_volume.bind_to(self.bn_volume),
            analysis.bn_surface_area.bind_to(self.bn_surface_area),
            analysis.bn_worthington.bind_to(self.bn_worthington),
            analysis.bn_bond_number.bind_to(self.bn_bond_number),
            analysis.bn_apex_coords_px.bind_to(self.bn_apex_coords),
            analysis.bn_rotation.bind_to(self.bn_image_angle),

            analysis.bn_residuals.bind_to(self.bn_residuals),

            analysis.bn_log.bind_to(self.bn_log_text),
        ]

        self._analysis_unbind_tasks.extend(
            db.unbind for db in data_bindings
        )

        event_connections = [
            analysis.bn_image.on_changed.connect(
                self._hdl_analysis_image_changed
            ),
            analysis.bn_drop_profile_extract.on_changed.connect(
                self._hdl_analysis_drop_profile_extract_changed
            ),
            analysis.bn_drop_profile_fit.on_changed.connect(
                self._hdl_analysis_drop_profile_fit_changed
            ),
        ]

        self._analysis_unbind_tasks.extend(
            ec.disconnect for ec in event_connections
        )

        self._hdl_analysis_image_changed()
        self._hdl_analysis_drop_profile_extract_changed()
        self._hdl_analysis_drop_profile_fit_changed()

    def _hdl_analysis_image_changed(self) -> None:
        analysis = self._bn_analysis.get()
        image = analysis.bn_image.get()
        if image is None:
            self.view.show_waiting_placeholder()
            return

        self.view.hide_waiting_placeholder()

        drop_region = analysis.bn_drop_region.get()
        assert drop_region is not None

        drop_image = image[drop_region.y0:drop_region.y1, drop_region.x0:drop_region.x1]
        self.bn_drop_image.set(drop_image)

    def _hdl_analysis_drop_profile_extract_changed(self) -> None:
        analysis = self._bn_analysis.get()
        drop_profile_ext = analysis.bn_drop_profile_extract.get()
        if drop_profile_ext is None:
            self.bn_drop_profile_extract.set(None)
            return

        drop_region = analysis.bn_drop_region.get()
        assert drop_region is not None

        drop_profile_ext_rel_drop_image = drop_profile_ext - drop_region.position
        self.bn_drop_profile_extract.set(drop_profile_ext_rel_drop_image)

    def _hdl_analysis_drop_profile_fit_changed(self) -> None:
        analysis = self._bn_analysis.get()
        drop_profile_fit = analysis.bn_drop_profile_fit.get()
        if drop_profile_fit is None:
            self.bn_drop_profile_fit.set(None)
            return

        drop_region = analysis.bn_drop_region.get()
        assert drop_region is not None

        drop_profile_fit_rel_drop_image = drop_profile_fit - drop_region.position
        self.bn_drop_profile_fit.set(drop_profile_fit_rel_drop_image)

    def _unbind_analysis(self) -> None:
        for task in self._analysis_unbind_tasks:
            task()
        self._analysis_unbind_tasks.clear()

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        self._unbind_analysis()
