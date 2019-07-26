import math
from typing import Optional

from gi.repository import Gtk, GObject

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable

progress_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@progress_cs.view()
class ProgressView(View['ProgressPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Grid(row_spacing=5)

        self._progress_bar = Gtk.ProgressBar(margin_top=5, hexpand=True, visible=True)
        self._widget.attach(self._progress_bar, 0, 0, 3, 1)

        self._time_elapsed_lbl = Gtk.Label(xalign=0, visible=True)
        self._progress_fraction_lbl = Gtk.Label(xalign=0.5, hexpand=True, visible=True)
        self._time_remaining_lbl = Gtk.Label(xalign=1, visible=True)
        self._complete_lbl = Gtk.Label(xalign=0.5, visible=True)

        self._widget.attach(self._time_elapsed_lbl, 0, 1, 1, 1)
        self._widget.attach(self._progress_fraction_lbl, 0, 1, 3, 1)
        self._widget.attach(self._time_remaining_lbl, 2, 1, 1, 1)
        self._widget.attach(self._complete_lbl, 0, 1, 3, 1)

        # Wiring things up

        self._progress_bar.bind_property(
            'fraction',                        # source_property
            self._progress_fraction_lbl,       # target
            'label',                           # target_property
            GObject.BindingFlags.SYNC_CREATE,  # flags
            lambda _, v: '{:.0%}'.format(v)    # transform_to
        )

        self.presenter.view_ready()

        return self._widget

    def set_progress(self, fraction: float) -> None:
        self._progress_bar.props.fraction = fraction

    def set_progress_label(self, label: Optional[str]) -> None:
        if label is None or label == '':
            self._complete_lbl.hide()
            self._progress_fraction_lbl.show()
            return

        self._progress_fraction_lbl.hide()

        self._complete_lbl.props.label = label
        self._complete_lbl.show()

    def set_time_elapsed(self, seconds: float) -> None:
        self._time_elapsed_lbl.props.label = (
            'Elapsed: {}'
            .format(pretty_time(seconds))
        )

    def set_time_remaining(self, seconds: float) -> None:
        if math.isnan(seconds) or seconds == 0:
            self._time_remaining_lbl.hide()
            return

        self._time_remaining_lbl.props.label = (
            'Remaining: {}'
            .format(pretty_time(seconds))
        )
        self._time_remaining_lbl.show()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@progress_cs.presenter(options=['in_progress', 'in_progress_label', 'in_time_elapsed', 'in_time_remaining'])
class ProgressPresenter(Presenter['ProgressView']):
    def _do_init(
            self,
            in_progress: Bindable[float],
            in_progress_label: Bindable[Optional[str]],
            in_time_elapsed: Bindable[float],
            in_time_remaining: Bindable[float],
    ) -> None:
        self._bn_progress_label = in_progress_label
        self._bn_progress = in_progress
        self._bn_time_elapsed = in_time_elapsed
        self._bn_time_remaining = in_time_remaining

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._bn_progress.on_changed.connect(
                self._hdl_progress_changed
            ),
            self._bn_progress_label.on_changed.connect(
                self._hdl_progress_label_changed
            ),
            self._bn_time_elapsed.on_changed.connect(
                self._hdl_time_elapsed_changed
            ),
            self._bn_time_remaining.on_changed.connect(
                self._hdl_time_remaining_changed
            ),
        ])

        self._hdl_progress_changed()
        self._hdl_progress_label_changed()
        self._hdl_time_elapsed_changed()
        self._hdl_time_remaining_changed()

    def _hdl_progress_changed(self) -> None:
        progress = self._bn_progress.get()
        self.view.set_progress(progress)

    def _hdl_progress_label_changed(self) -> None:
        label = self._bn_progress_label.get()
        self.view.set_progress_label(label)

    def _hdl_time_elapsed_changed(self) -> None:
        elapsed = self._bn_time_elapsed.get()
        self.view.set_time_elapsed(elapsed)

    def _hdl_time_remaining_changed(self) -> None:
        remaining = self._bn_time_remaining.get()
        self.view.set_time_remaining(remaining)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()


# Helper function

def pretty_time(seconds: float) -> str:
    if not math.isfinite(seconds):
        return ''

    seconds = round(seconds)

    s = seconds % 60
    seconds //= 60
    m = seconds % 60
    seconds //= 60
    h = seconds

    return '{h:0>2}:{m:0>2}:{s:0>2}'.format(h=h, m=m, s=s)
