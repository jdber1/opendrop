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


from typing import Optional, Any

import cairo
import numpy as np

from opendrop.features import colorize_labels
from opendrop.geometry import Rect2
from opendrop.widgets.canvas import ImageArtist
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.common.image_processing.plugins.preview import (
    AcquirerController,
    ImageSequenceAcquirerController,
    image_sequence_navigator_cs,
)
from opendrop.app.conan.services.features import ConanFeatures

from .model import ConanPreviewPluginModel


conan_preview_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@conan_preview_plugin_cs.view(options=['view_context', 'z_index'])
class ConanPreviewPluginView(View['ConanPreviewPluginPresenter', None]):
    def _do_init(self, view_context: ImageProcessorPluginViewContext, z_index: int) -> None:
        self._view_context = view_context
        self._canvas = self._view_context.canvas

        self._image_sequence_navigator_cid = None  # type: Optional[Any]

        self._image_artist = ImageArtist()
        self._canvas.add_artist(self._image_artist, z_index=z_index)

        self._features_artist = ImageArtist()
        self._canvas.add_artist(self._features_artist, z_index=z_index)

        self.presenter.view_ready()

    def set_image(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self._image_artist.clear_data()
            return

        width = image.shape[1]
        height = image.shape[0]
        self._image_artist.extents = Rect2(0, 0, width, height)
        self._image_artist.set_array(image)
        self._canvas.set_content_size(width, height)

        # Set zoom to minimum, i.e. scale image so it always fits.
        self._canvas.zoom(0)

    def set_features(self, features: Optional[ConanFeatures]) -> None:
        if features is None:
            self._features_artist.clear_data()
            return

        if features.labels is None:
            self._features_artist.clear_data()
            return

        data = colorize_labels(
            features.labels,
            colors=np.array([
                0x00000000,
                0xffbbbbff,  # All edges
                0xff0000ff,  # Drop edges
            ], dtype=np.uint32).view(np.uint8).reshape(-1, 4),
        )

        width = features.labels.shape[1]
        height = features.labels.shape[0]

        self._features_artist.extents = Rect2(0, 0, width, height)
        self._features_artist.set_data(data, cairo.Format.ARGB32, width, height)

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
        self._canvas.remove_artist(self._image_artist)
        self._canvas.remove_artist(self._features_artist)


@conan_preview_plugin_cs.presenter(options=['model'])
class ConanPreviewPluginPresenter(Presenter['ConanPreviewPluginView']):
    def _do_init(self, model: ConanPreviewPluginModel) -> None:
        self._model = model
        self.__event_connections = []

    def view_ready(self) -> None:
        self._model.watch()

        self.__event_connections.extend([
            self._model.bn_source_image.on_changed.connect(
                self._update_image,
            ),
            self._model.bn_features.on_changed.connect(
                self._update_features,
            ),
            self._model.bn_acquirer_controller.on_changed.connect(
                self._hdl_model_acquirer_controller_changed,
            ),
        ])

        self._update_image()
        self._update_features()
        self._hdl_model_acquirer_controller_changed()

    def _update_image(self) -> None:
        source_image = self._model.bn_source_image.get()
        self.view.set_image(source_image)

    def _update_features(self) -> None:
        features = self._model.bn_features.get()
        self.view.set_features(features)

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
