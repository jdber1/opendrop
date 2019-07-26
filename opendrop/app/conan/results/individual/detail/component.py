import math
from typing import Optional

from gi.repository import Gtk

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable, BoxBindable
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

        self.bn_image = BoxBindable(None)

        self.bn_left_angle = BoxBindable(math.nan)
        self.bn_left_point = BoxBindable(Vector2(math.nan, math.nan))
        self.bn_right_angle = BoxBindable(math.nan)
        self.bn_right_point = BoxBindable(Vector2(math.nan, math.nan))

        self.bn_surface_line = BoxBindable(None)

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
            analysis.bn_image.bind(self.bn_image),
            analysis.bn_left_angle.bind(self.bn_left_angle),
            analysis.bn_left_point.bind(self.bn_left_point),
            analysis.bn_right_angle.bind(self.bn_right_angle),
            analysis.bn_right_point.bind(self.bn_right_point),
            analysis.bn_surface_line.bind(self.bn_surface_line),
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
