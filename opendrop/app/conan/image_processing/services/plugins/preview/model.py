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


import asyncio
from typing import Optional, Callable, Hashable

import numpy as np

from opendrop.app.common.services.acquisition import ImageAcquisitionService, ImageSequenceAcquirer, CameraAcquirer
from opendrop.app.common.image_processing.plugins.preview.model import (
    AcquirerController,
    ImageSequenceAcquirerController,
    CameraAcquirerController
)
from opendrop.app.conan.services.params import ConanParamsFactory
from opendrop.app.conan.services.features import ConanFeaturesService, ConanFeatures
from opendrop.utility.bindable import VariableBindable, AccessorBindable
from opendrop.utility.bindable.typing import Bindable


class ConanPreviewPluginModel:
    def __init__(
            self, *,
            image_acquisition: ImageAcquisitionService,
            params_factory: ConanParamsFactory,
            features_service: ConanFeaturesService,
    ) -> None:
        self._image_acquisition = image_acquisition
        self._params_factory = params_factory
        self._features_service = features_service

        self._watchers = 0

        self._acquirer_controller = None  # type: Optional[AcquirerController]

        self.bn_acquirer_controller = AccessorBindable(
            getter=lambda: self._acquirer_controller
        )

        self.bn_source_image = VariableBindable(None)
        self.bn_features = VariableBindable(None)

        self._image_acquisition.bn_acquirer.on_changed.connect(
            self._update_acquirer_controller,
        )

    def watch(self) -> None:
        self._watchers += 1
        self._update_acquirer_controller()

    def unwatch(self) -> None:
        self._watchers -= 1
        self._update_acquirer_controller()

    def _update_acquirer_controller(self) -> None:
        self._destroy_acquirer_controller()

        if self._watchers <= 0:
            return

        new_acquirer = self._image_acquisition.bn_acquirer.get()

        if isinstance(new_acquirer, ImageSequenceAcquirer):
            new_acquirer_controller = ConanImageSequenceAcquirerController(
                acquirer=new_acquirer,
                params_factory=self._params_factory,
                features_service=self._features_service,
                source_image_out=self.bn_source_image,
                show_features=self._show_features,
            )
        elif isinstance(new_acquirer, CameraAcquirer):
            new_acquirer_controller = ConanCameraAcquirerController(
                acquirer=new_acquirer,
                params_factory=self._params_factory,
                features_service=self._features_service,
                source_image_out=self.bn_source_image,
                show_features=self._show_features,
            )
        elif new_acquirer is None:
            new_acquirer_controller = None
        else:
            raise ValueError(
                "Unknown acquirer '{}'"
                .format(new_acquirer)
            )

        self._acquirer_controller = new_acquirer_controller
        self.bn_acquirer_controller.poke()

    def _show_features(self, features: Optional[ConanFeatures]) -> None:
        if features is None:
            self.bn_features.set(None)
            return

        self.bn_features.set(features)

    def _destroy_acquirer_controller(self) -> None:
        acquirer_controller = self._acquirer_controller
        if acquirer_controller is None:
            return

        acquirer_controller.destroy()

        self._acquirer_controller = None


class ConanImageSequenceAcquirerController(ImageSequenceAcquirerController):
    def __init__(
            self, *,
            acquirer: ImageSequenceAcquirer,
            params_factory: ConanParamsFactory,
            features_service: ConanFeaturesService,
            source_image_out: Bindable[Optional[np.ndarray]],
            show_features: Callable,
    ) -> None:
        self._params_factory = params_factory
        self._features_service = features_service
        self._show_features = show_features

        self.__destroyed = False

        self._extracted_features = {}
        self._images = {}
        self._current_image = None
        self._current_preview = None

        super().__init__(
            acquirer=acquirer,
            source_image_out=source_image_out,
        )

        self._params_factory_changed_id = \
            params_factory.connect('changed', self._params_factory_chagned)

    def _params_factory_chagned(self, *_) -> None:
        for fut in self._extracted_features.values():
            fut.cancel()

        self._extracted_features = {}
        self._queue_update_preview()

    def _on_image_registered(self, image_id: Hashable, image: np.ndarray) -> None:
        self._images[image_id] = image

    def _on_image_deregistered(self, image_id: Hashable) -> None:
        del self._images[image_id]
        if image_id in self._extracted_features:
            del self._extracted_features[image_id]

    def _on_image_changed(self, image_id: Hashable) -> None:
        self._current_image = image_id
        self._queue_update_preview()

    def _queue_update_preview(self, *_) -> None:
        if self.__destroyed: return

        image_id = self._current_image
        image = self._images[self._current_image]

        if image_id not in self._extracted_features:
            fut = self._features_service.extract(image, labels=True)
            self._extracted_features[image_id] = fut
            fut.add_done_callback(self._queue_update_preview)

        fut = self._extracted_features[image_id]
        if not fut.done() and self._current_preview is self._current_image:
            return

        if not fut.done():
            extracted_features = None
        else:
            extracted_features = fut.result()

        self._update_preview(extracted_features)

    def _update_preview(self, extracted_feature: Optional[ConanFeatures]) -> None:
        self._show_features(extracted_feature)
        self._current_preview = self._current_image

    def destroy(self) -> None:
        self.__destroyed = True
        self._params_factory.disconnect(self._params_factory_changed_id)
        super().destroy()


class ConanCameraAcquirerController(CameraAcquirerController):
    def __init__(
            self, *,
            acquirer: CameraAcquirer,
            params_factory: ConanParamsFactory,
            features_service: ConanFeaturesService,
            source_image_out: Bindable[Optional[np.ndarray]],
            show_features: Callable,
    ) -> None:
        self._params_factory = params_factory
        self._features_service = features_service
        self._show_features = show_features

        self.__destroyed = False

        self._extracted_feature_fut = None

        super().__init__(
            acquirer=acquirer,
            source_image_out=source_image_out,
        )

        self._source_image_changed_conn = source_image_out.on_changed.connect(self._source_image_changed)

    def _source_image_changed(self) -> None:
        self._queue_update_preview()

    def _queue_update_preview(self) -> None:
        if self.__destroyed: return

        image = self._source_image_out.get()
        if image is None:
            return

        old = self._extracted_feature_fut
        if old is not None and not old.done():
            return

        fut = self._features_service.extract(
            image,
            self._params_factory.create(),
            labels=True,
        )
        self._extracted_feature_fut = fut
        fut.add_done_callback(self._update_preview)

    def _update_preview(self, fut: asyncio.Future) -> None:
        if fut.cancelled():
            return

        features = fut.result()
        self._show_features(features)

    def destroy(self) -> None:
        self.__destroyed = True
        if self._extracted_feature_fut is not None:
            self._extracted_feature_fut.cancel()
        self._source_image_changed_conn.disconnect()
        super().destroy()
