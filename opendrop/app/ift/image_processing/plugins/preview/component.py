from typing import Optional, Tuple, Any

import numpy as np

from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.common.image_processing.plugins.preview import AcquirerController, ImageSequenceAcquirerController, \
    image_sequence_navigator_cs
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.geometry import Rect2
from opendrop.utility.gmisc import pixbuf_from_array
from opendrop.widgets.render.objects import PixbufFill, Polyline, MaskFill
from .model import IFTPreviewPluginModel

ift_preview_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@ift_preview_plugin_cs.view(options=['view_context', 'z_index'])
class IFTPreviewPluginView(View['IFTPreviewPluginPresenter', None]):
    def _do_init(self, view_context: ImageProcessorPluginViewContext, z_index: int) -> None:
        self._view_context = view_context
        self._render = self._view_context.render

        self._image_sequence_navigator_cid = None  # type: Optional[Any]

        self._background_ro = PixbufFill(
            z_index=z_index,
        )
        self._render.add_render_object(self._background_ro)

        self._edge_detection_ro = MaskFill(
            color=(0.5, 0.5, 1.0),
            z_index=z_index,
        )
        self._render.add_render_object(self._edge_detection_ro)

        self._drop_profile_ro = Polyline(
            stroke_color=(0.0, 0.5, 1.0),
            stroke_width=2,
            z_index=z_index,
        )
        self._render.add_render_object(self._drop_profile_ro)

        self._needle_profile_ro = Polyline(
            stroke_color=(0.0, 0.5, 1.0),
            stroke_width=2,
            z_index=z_index,
        )
        self._render.add_render_object(self._needle_profile_ro)

        self.presenter.view_ready()

    def set_background_image(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self._background_ro.props.pixbuf = None
            return

        self._background_ro.props.pixbuf = pixbuf_from_array(image)

        self._render.props.canvas_size = image.shape[1::-1]
        self._render.viewport_extents = Rect2(pos=(0, 0), size=image.shape[1::-1])

    def set_edge_detection(self, mask: Optional[np.ndarray]) -> None:
        self._edge_detection_ro.props.mask = mask

    def set_drop_profile(self, drop_profile: Optional[np.ndarray]) -> None:
        if drop_profile is None:
            self._drop_profile_ro.props.polyline = None
            return

        self._drop_profile_ro.props.polyline = [drop_profile]

    def set_needle_profile(self, needle_profile: Optional[Tuple[np.ndarray, np.ndarray]]) -> None:
        self._needle_profile_ro.props.polyline = needle_profile

    def show_image_sequence_navigator(self) -> None:
        if self._image_sequence_navigator_cid is not None:
            return

        self._image_sequence_navigator_cid, nav_area = \
            self.new_component(
                image_sequence_navigator_cs.factory(
                    model=self.presenter.acquirer_controller
                )
            )

        nav_area.show()
        self._view_context.extras_area.add(nav_area)

    def hide_image_sequence_navigator(self) -> None:
        if self._image_sequence_navigator_cid is None:
            return

        self.remove_component(
            self._image_sequence_navigator_cid
        )

        self._image_sequence_navigator_cid = None

    def _do_destroy(self) -> None:
        self._render.remove_render_object(self._background_ro)
        self._render.remove_render_object(self._edge_detection_ro)
        self._render.remove_render_object(self._drop_profile_ro)
        self._render.remove_render_object(self._needle_profile_ro)


@ift_preview_plugin_cs.presenter(options=['model'])
class IFTPreviewPluginPresenter(Presenter['IFTPreviewPluginView']):
    def _do_init(self, model: IFTPreviewPluginModel) -> None:
        self._model = model
        self.__event_connections = []

    def view_ready(self) -> None:
        self._model.watch()

        self.__event_connections.extend([
            self._model.bn_source_image.on_changed.connect(
                self._update_preview_source_image,
            ),
            self._model.bn_edge_detection.on_changed.connect(
                self._update_edge_detection,
            ),
            self._model.bn_drop_profile.on_changed.connect(
                self._update_drop_profile,
            ),
            self._model.bn_needle_profile.on_changed.connect(
                self._update_needle_profile,
            ),
            self._model.bn_acquirer_controller.on_changed.connect(
                self._hdl_model_acquirer_controller_changed,
            )
        ])

        self._update_preview_source_image()
        self._update_edge_detection()
        self._update_drop_profile()
        self._update_needle_profile()
        self._hdl_model_acquirer_controller_changed()

    def _update_preview_source_image(self) -> None:
        source_image = self._model.bn_source_image.get()
        self.view.set_background_image(source_image)

    def _update_edge_detection(self) -> None:
        edge_detection = self._model.bn_edge_detection.get()
        self.view.set_edge_detection(edge_detection)

    def _update_drop_profile(self) -> None:
        drop_profile = self._model.bn_drop_profile.get()
        self.view.set_drop_profile(drop_profile)

    def _update_needle_profile(self) -> None:
        needle_profile = self._model.bn_needle_profile.get()
        self.view.set_needle_profile(needle_profile)

    def _hdl_model_acquirer_controller_changed(self) -> None:
        acquirer_controller = self.acquirer_controller

        if isinstance(acquirer_controller, ImageSequenceAcquirerController):
            self.view.show_image_sequence_navigator()
        else:
            self.view.hide_image_sequence_navigator()

    @property
    def acquirer_controller(self) -> Optional[AcquirerController]:
        return self._model.bn_acquirer_controller.get()

    def _do_destroy(self):
        for ec in self.__event_connections:
            ec.disconnect()

        self._model.unwatch()
