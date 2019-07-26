from typing import Optional, Callable, Hashable, Tuple

import numpy as np

from opendrop.app.common.image_acquirer import ImageSequenceAcquirer, CameraAcquirer
from opendrop.app.common.image_acquisition import ImageAcquisitionModel
from opendrop.app.common.image_processing.plugins.preview.model import (
    AcquirerController,
    ImageSequenceAcquirerController,
    CameraAcquirerController)
from opendrop.app.ift.analysis import FeatureExtractorParams, FeatureExtractor
from opendrop.utility.bindable import BoxBindable, Bindable, AccessorBindable


class IFTPreviewPluginModel:
    def __init__(
            self, *,
            image_acquisition: ImageAcquisitionModel,
            feature_extractor_params: FeatureExtractorParams,
            do_extract_features: Callable[[Bindable[np.ndarray]], FeatureExtractor]
    ) -> None:
        self._image_acquisition = image_acquisition
        self._feature_extractor_params = feature_extractor_params
        self._do_extract_features = do_extract_features

        self._watchers = 0

        self._acquirer_controller = None  # type: Optional[AcquirerController]

        self.bn_acquirer_controller = AccessorBindable(
            getter=lambda: self._acquirer_controller
        )

        self.bn_source_image = BoxBindable(None)  # type: Bindable[Optional[np.ndarray]]
        self.bn_edge_detection = BoxBindable(None)  # type: Bindable[Optional[np.ndarray]]
        self.bn_drop_profile = BoxBindable(None)  # type: Bindable[Optional[np.ndarray]]
        self.bn_needle_profile = BoxBindable(None)  # type: Bindable[Optional[Tuple[np.ndarray, np.ndarray]]]

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
            new_acquirer_controller = IFTImageSequenceAcquirerController(
                acquirer=new_acquirer,
                do_extract_features=self._do_extract_features,
                source_image_out=self.bn_source_image,
                edge_detection_out=self.bn_edge_detection,
                drop_profile_out=self.bn_drop_profile,
                needle_profile_out=self.bn_needle_profile,
            )
        elif isinstance(new_acquirer, CameraAcquirer):
            new_acquirer_controller = IFTCameraAcquirerController(
                acquirer=new_acquirer,
                do_extract_features=self._do_extract_features,
                source_image_out=self.bn_source_image,
                edge_detection_out=self.bn_edge_detection,
                drop_profile_out=self.bn_drop_profile,
                needle_profile_out=self.bn_needle_profile,
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

    def _destroy_acquirer_controller(self) -> None:
        acquirer_controller = self._acquirer_controller
        if acquirer_controller is None:
            return

        acquirer_controller.destroy()

        self._acquirer_controller = None


class IFTImageSequenceAcquirerController(ImageSequenceAcquirerController):
    def __init__(
            self, *,
            acquirer: ImageSequenceAcquirer,
            do_extract_features: Callable[[Bindable[np.ndarray]], FeatureExtractor],
            source_image_out: Bindable[Optional[np.ndarray]],
            edge_detection_out: Bindable[Optional[np.ndarray]],
            drop_profile_out: Bindable[Optional[np.ndarray]],
            needle_profile_out: Bindable[Optional[Tuple[np.ndarray, np.ndarray]]]
    ) -> None:
        self._do_extract_features = do_extract_features

        self._edge_detection_out = edge_detection_out
        self._drop_profile_out = drop_profile_out
        self._needle_profile_out = needle_profile_out

        self._extracted_features = {}

        self._showing_extracted_feature = None  # type: Optional[FeatureExtractor]
        self._sef_cleanup_tasks = []

        super().__init__(
            acquirer=acquirer,
            source_image_out=source_image_out,
        )

    def _on_image_registered(self, image_id: Hashable, image: np.ndarray) -> None:
        extracted_feature = self._do_extract_features(BoxBindable(image))
        self._extracted_features[image_id] = extracted_feature

    def _on_image_deregistered(self, image_id: Hashable) -> None:
        del self._extracted_features[image_id]

    def _on_image_changed(self, image_id: Hashable) -> None:
        extracted_feature = self._extracted_features[image_id]
        self._set_showing_extracted_feature(extracted_feature)

    def _set_showing_extracted_feature(self, extracted_feature: Optional[FeatureExtractor]) -> None:
        self._unbind_showing_extracted_feature()

        self._showing_extracted_feature = extracted_feature

        if extracted_feature is None:
            self._edge_detection_out.set(None)
            return

        self._bind_showing_extracted_feature()

    def _bind_showing_extracted_feature(self) -> None:
        extracted_feature = self._showing_extracted_feature

        data_bindings = [
            extracted_feature.bn_edge_detection.bind(
                self._edge_detection_out
            ),
            extracted_feature.bn_drop_profile_px.bind(
                self._drop_profile_out
            ),
            extracted_feature.bn_needle_profile_px.bind(
                self._needle_profile_out
            ),
        ]

        self._sef_cleanup_tasks.extend([
            db.unbind
            for db in data_bindings
        ])

    def _unbind_showing_extracted_feature(self) -> None:
        for task in self._sef_cleanup_tasks:
            task()
        self._sef_cleanup_tasks.clear()

    def destroy(self) -> None:
        super().destroy()
        self._set_showing_extracted_feature(None)
        self._extracted_features.clear()


class IFTCameraAcquirerController(CameraAcquirerController):
    def __init__(
            self, *,
            acquirer: CameraAcquirer,
            do_extract_features: Callable[[Bindable[np.ndarray]], FeatureExtractor],
            source_image_out: Bindable[Optional[np.ndarray]],
            edge_detection_out: Bindable[Optional[np.ndarray]],
            drop_profile_out: Bindable[Optional[np.ndarray]],
            needle_profile_out: Bindable[Optional[Tuple[np.ndarray, np.ndarray]]]
    ) -> None:
        self._do_extract_features = do_extract_features

        self._edge_detection_out = edge_detection_out
        self._drop_profile_out = drop_profile_out
        self._needle_profile_out = needle_profile_out

        self._extracted_feature = None  # type: Optional[FeatureExtractor]
        self._ef_cleanup_tasks = []

        super().__init__(
            acquirer=acquirer,
            source_image_out=source_image_out,
        )

    def _on_camera_changed(self) -> None:
        self._unbind_extracted_feature()

        new_extracted_feature = self._do_extract_features(self._source_image_out)
        self._extracted_feature = new_extracted_feature

        self._bind_extracted_feature()

    def _bind_extracted_feature(self) -> None:
        extracted_feature = self._extracted_feature

        data_bindings = [
            extracted_feature.bn_edge_detection.bind(
                self._edge_detection_out
            ),
            extracted_feature.bn_drop_profile_px.bind(
                self._drop_profile_out
            ),
            extracted_feature.bn_needle_profile_px.bind(
                self._needle_profile_out
            ),
        ]

        self._ef_cleanup_tasks.extend([
            db.unbind
            for db in data_bindings
        ])

    def _unbind_extracted_feature(self) -> None:
        for task in self._ef_cleanup_tasks:
            task()
        self._ef_cleanup_tasks.clear()

    def destroy(self) -> None:
        super().destroy()

        self._unbind_extracted_feature()
        self._extracted_feature = None
