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
import itertools
from typing import Optional, Hashable, Iterable, MutableSequence

from gi.repository import GLib
import numpy as np

from opendrop.app.common.services.acquisition import ImageSequenceAcquirer, CameraAcquirer
from opendrop.utility.bindable import AccessorBindable
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.misc import clamp


class AcquirerController:
    def destroy(self) -> None:
        pass


class ImageSequenceAcquirerController(AcquirerController):
    class _ImageRegistration:
        def __init__(self, image_id: Hashable, image: np.ndarray) -> None:
            self.image_id = image_id
            self.image = image

    def __init__(
            self, *,
            acquirer: ImageSequenceAcquirer,
            source_image_out: Bindable[Optional[np.ndarray]]
    ) -> None:
        self._acquirer = acquirer
        self._source_image_out = source_image_out

        self._image_registry = []  # type: MutableSequence[self._ImageRegistration]

        self.bn_num_images = AccessorBindable(
            getter=self._get_num_images,
        )

        self._showing_image_index = None  # type: Optional[int]
        self.bn_showing_image_index = AccessorBindable(
            getter=self._get_showing_image_index,
            setter=self._set_showing_image_index,
        )

        self._showing_image_id = None  # type: Optional[Hashable]

        self.__event_connections = [
            acquirer.bn_images.on_changed.connect(
                self._hdl_acquirer_images_changed
            ),
        ]
        self._hdl_acquirer_images_changed()

    def _hdl_acquirer_images_changed(self) -> None:
        self._showing_image_index = None
        self._update_image_registry()
        self._update_showing_image()

    def _update_image_registry(self) -> None:
        acquirer_images = list(self._acquirer.bn_images.get())

        for image_reg in tuple(self._get_unassociated_registered_images(acquirer_images)):
            self._image_registry.remove(image_reg)
            self._on_image_deregistered(image_reg.image_id)

        for image in self._filter_unregistered_images(acquirer_images):
            new_image_reg = self._ImageRegistration(
                image_id=id(image),
                image=image,
            )
            self._image_registry.append(new_image_reg)
            self._on_image_registered(
                image_id=new_image_reg.image_id,
                image=image,
            )

        self.bn_num_images.poke()

    def _filter_unregistered_images(self, images: Iterable[np.ndarray]) -> Iterable[np.ndarray]:
        return itertools.filterfalse(self._is_image_registered, images)

    def _is_image_registered(self, image: np.ndarray) -> bool:
        try:
            self._get_image_reg_by_image(image)
        except ValueError:
            return False
        else:
            return True

    def _get_unassociated_registered_images(self, images: Iterable[np.ndarray]) -> Iterable[_ImageRegistration]:
        return (
            image_reg
            for image_reg in self._image_registry
            if not self._is_registered_image_associated(images, image_reg)
        )

    @staticmethod
    def _is_registered_image_associated(images: Iterable[np.ndarray], image_reg: _ImageRegistration) -> bool:
        for image in images:
            if np.array_equal(image_reg.image, image):
                return True
        else:
            return False

    def _update_showing_image(self) -> None:
        acquirer_images = list(self._acquirer.bn_images.get())
        if self._showing_image_index is None and len(acquirer_images) > 0:
            self._showing_image_index = 0
            self.bn_showing_image_index.poke()

        if self._showing_image_index is None:
            return

        new_showing_image_reg = self._get_image_reg_by_image(
            image=acquirer_images[self._showing_image_index]
        )

        new_showing_image_id = new_showing_image_reg.image_id

        if new_showing_image_id == self._showing_image_id:
            return

        self._showing_image_id = new_showing_image_id
        self._on_image_changed(new_showing_image_id)
        self._update_source_image_out()

    def _update_source_image_out(self) -> None:
        image_reg = self._get_image_reg_by_image_id(
            image_id=self._showing_image_id,
        )

        image = image_reg.image

        self._source_image_out.set(image)

    def _get_image_reg_by_image(self, image: np.ndarray) -> _ImageRegistration:
        for image_reg in self._image_registry:
            if np.array_equal(image_reg.image, image):
                return image_reg
        else:
            raise ValueError(
                "No _ImageRegistration found for image '{}'"
                .format(image)
            )

    def _get_image_reg_by_image_id(self, image_id: Hashable) -> _ImageRegistration:
        for image_reg in self._image_registry:
            if image_reg.image_id == image_id:
                return image_reg
        else:
            raise ValueError(
                "No _ImageRegistration found for image_id '{}'"
                .format(image_id)
            )

    def _get_showing_image_index(self) -> Optional[int]:
        return self._showing_image_index

    def _set_showing_image_index(self, idx: Optional[int]) -> None:
        if idx is None:
            return

        idx = clamp(idx, 0, self.bn_num_images.get() - 1)
        self._showing_image_index = idx
        self._update_showing_image()

    def _get_num_images(self) -> int:
        return len(self._acquirer.bn_images.get())

    def _on_image_registered(self, image_id: Hashable, image: np.ndarray) -> None:
        pass

    def _on_image_deregistered(self, image_id: Hashable) -> None:
        pass

    def _on_image_changed(self, image_id: Hashable) -> None:
        pass

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()


class CameraAcquirerController(AcquirerController):
    #  PREVIEW_FRAME_RATE = 20

    def __init__(
            self, *,
            acquirer: CameraAcquirer,
            source_image_out: Bindable[Optional[np.ndarray]]
    ) -> None:
        self._loop = asyncio.get_event_loop()

        self._acquirer = acquirer
        self._source_image_out = source_image_out

        self._update_loop_handle = None

        self.__event_connections = [
            acquirer.bn_camera.on_changed.connect(
                self._hdl_acquirer_camera_changed
            )
        ]

        self._hdl_acquirer_camera_changed()

    def _hdl_acquirer_camera_changed(self) -> None:
        camera = self._acquirer.bn_camera.get()

        if camera is None:
            self._cancel_pending_update_loop()
        else:
            self._update_loop()

        self._on_camera_changed()

    def _update_loop(self, *_) -> None:
        self._cancel_pending_update_loop()

        self._update_source_image_out()

        self._update_loop_handle = GLib.idle_add(
            priority=GLib.PRIORITY_LOW,
            function=self._update_loop,
        )
        #  self._update_loop_handle = self._loop.call_later(
            #  delay=1 / self.PREVIEW_FRAME_RATE,
            #  callback=self._update_loop,
        #  )

    def _update_source_image_out(self) -> None:
        camera = self._acquirer.bn_camera.get()
        if camera is None:
            return

        self._source_image_out.set(
            camera.capture()
        )

    def _cancel_pending_update_loop(self) -> None:
        if self._update_loop_handle is None:
            return

        GLib.source_remove(self._update_loop_handle)
        self._update_loop_handle = None

        #  self._update_loop_handle.cancel()
        #  self._update_loop_handle = None

    def _on_camera_changed(self) -> None:
        pass

    def destroy(self) -> None:
        self._cancel_pending_update_loop()

        for ec in self.__event_connections:
            ec.disconnect()
