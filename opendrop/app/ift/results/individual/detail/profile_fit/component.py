from typing import Optional

import cv2
import numpy as np
from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable

drop_fit_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@drop_fit_cs.view()
class DropFitView(View['DropFitPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
        from matplotlib.figure import Figure
        from matplotlib.image import AxesImage

        self._widget = Gtk.Grid()

        figure = Figure(tight_layout=True)

        self._figure_canvas = FigureCanvas(figure)
        self._figure_canvas.props.hexpand = True
        self._figure_canvas.props.vexpand = True
        self._figure_canvas.show()
        self._widget.add(self._figure_canvas)

        # Axes
        self._axes = figure.add_subplot(1, 1, 1)
        self._axes.set_aspect('equal', 'box')
        self._axes.xaxis.tick_top()
        for item in (*self._axes.get_xticklabels(), *self._axes.get_yticklabels()):
            item.set_fontsize(8)

        self._axes_bg_image = AxesImage(ax=self._axes)

        # Placeholder transparent 1x1 image (rgba format)
        self._axes_bg_image.set_data(np.zeros((1, 1, 4)))
        self._axes.add_image(self._axes_bg_image)

        self._profile_extract_line = self._axes.plot([], linestyle='-', color='#0080ff', linewidth=1.5)[0]
        self._profile_fit_line = self._axes.plot([], linestyle='-', color='#ff0080', linewidth=1)[0]

        self.presenter.view_ready()

        return self._widget

    def set_drop_image(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self._axes.set_axis_off()
            self._axes_bg_image.set_data(np.zeros((1, 1, 4)))
            self._figure_canvas.queue_draw()
            return

        self._axes.set_axis_on()

        # Use a scaled down image so it draws faster.
        thumb_size = (min(400, image.shape[1]), min(400, image.shape[0]))
        image_thumb = cv2.resize(image, dsize=thumb_size)
        self._axes_bg_image.set_data(image_thumb)

        self._axes_bg_image.set_extent((0, image.shape[1], image.shape[0], 0))
        self._figure_canvas.queue_draw()

    def set_drop_profile_extract(self, profile: Optional[np.ndarray]) -> None:
        if profile is None:
            self._profile_fit_line.set_visible(False)
            self._figure_canvas.queue_draw()
            return

        self._profile_fit_line.set_data(profile.T)
        self._profile_fit_line.set_visible(True)
        self._figure_canvas.queue_draw()

    def set_drop_profile_fit(self, profile: Optional[np.ndarray]) -> None:
        if profile is None:
            self._profile_extract_line.set_visible(False)
            self._figure_canvas.queue_draw()
            return

        self._profile_extract_line.set_data(profile.T)
        self._profile_extract_line.set_visible(True)
        self._figure_canvas.queue_draw()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@drop_fit_cs.presenter(options=['in_drop_image', 'in_drop_profile_extract', 'in_drop_profile_fit'])
class DropFitPresenter(Presenter['DropFitView']):
    def _do_init(
            self,
            in_drop_image: Bindable[Optional[np.ndarray]],
            in_drop_profile_extract: Bindable[Optional[np.ndarray]],
            in_drop_profile_fit: Bindable[Optional[np.ndarray]],
    ) -> None:
        self._bn_drop_image = in_drop_image
        self._bn_drop_profile_extract = in_drop_profile_extract
        self._bn_drop_profile_fit = in_drop_profile_fit

        self.__event_connections = []

    def view_ready(self):
        self.__event_connections.extend([
            self._bn_drop_image.on_changed.connect(
                self._hdl_drop_image_changed
            ),
            self._bn_drop_profile_extract.on_changed.connect(
                self._hdl_drop_profile_extract_changed
            ),
            self._bn_drop_profile_fit.on_changed.connect(
                self._hdl_drop_profile_fit_changed
            ),
        ])

        self._hdl_drop_image_changed()
        self._hdl_drop_profile_extract_changed()
        self._hdl_drop_profile_fit_changed()

    def _hdl_drop_image_changed(self) -> None:
        drop_image = self._bn_drop_image.get()
        self.view.set_drop_image(drop_image)

    def _hdl_drop_profile_extract_changed(self) -> None:
        drop_profile_extract = self._bn_drop_profile_extract.get()
        self.view.set_drop_profile_extract(drop_profile_extract)

    def _hdl_drop_profile_fit_changed(self) -> None:
        drop_profile_fit = self._bn_drop_profile_fit.get()
        self.view.set_drop_profile_fit(drop_profile_fit)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
