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


import os
from pathlib import Path
from typing import Tuple, Optional, NamedTuple, Sequence

import cv2

import numpy as np

try:
    import genicam.gentl
    import opendrop.vendor.harvesters.core as harvesters
    GENICAM_ENABLED = True
except ModuleNotFoundError:
    from unittest.mock import Mock
    genicam = Mock()
    harvesters = Mock()
    GENICAM_ENABLED = False

from opendrop.utility.bindable import VariableBindable, AccessorBindable
from opendrop.utility.bindable.typing import ReadBindable
from opendrop.utility.events import EventConnection
from .camera import CameraAcquirer, Camera, CameraCaptureError


GenicamCameraInfo = NamedTuple('GenicamCameraInfo', [
    ("camera_id", str),
    ("vendor", str),
    ("model", str),
    ("name", str),
    ("tl_type", str),
    ("version", str),
])

class GenicamAcquirer(CameraAcquirer):
    def __init__(self):
        super().__init__()

        self._harvester = harvesters.Harvester()

        for cti_path in os.environ.get('GENICAM_GENTL64_PATH', '').split(os.pathsep):
            for cti_file in map(str, Path(cti_path).glob('*.cti')):
                self._harvester.add_file(cti_file)

        self._camera_id = None
        self.bn_camera_id = AccessorBindable(self._get_camera_id)  # type: ReadBindable[Optional[str]]

        self._camera_alive_changed_conn = None  # type: Optional[EventConnection]

    def _get_camera_id(self) -> Optional[str]:
        if not GENICAM_ENABLED: return
        return self._camera_id

    def update(self) -> None:
        if not GENICAM_ENABLED: return
        self._harvester.update()

    def enumerate_cameras(self) -> Sequence[GenicamCameraInfo]:
        if not GENICAM_ENABLED: return ()
        raw = self._harvester.device_info_list
        out = []

        for raw_info in raw:
            camera_id = raw_info.id_
            vendor = raw_info.vendor
            model = raw_info.model
            tl_type = raw_info.tl_type

            try:
                name = raw_info.user_defined_name
            except genicam.gentl.NotImplementedException:
                name = '{} {} ({})'.format(vendor, model, id)

            try:
                version = raw_info.version
            except genicam.gentl.NotImplementedException:
                version = 'n/a'

            out.append(GenicamCameraInfo(
                camera_id=camera_id,
                vendor=vendor,
                model=model,
                name=name,
                tl_type=tl_type,
                version=version,
            ))

        return out

    def open_camera(self, id_: str) -> None:
        if not GENICAM_ENABLED:
            raise RuntimeError("GenICam libraries not found")

        try:
            ia = self._harvester.create_image_acquirer(id_=id_)
        except ValueError:
            raise ValueError("Failed to open '{}'".format(id_))

        try:
            new_camera = GenicamCamera(ia)
        except ValueError:
            raise ValueError("Failed to open '{}'".format(id_))

        self.remove_current_camera(_poke_current_camera_id=False)

        self._camera_alive_changed_conn = new_camera.bn_alive.on_changed.connect(self._camera_alive_changed)
        self.bn_camera.set(new_camera)

        self._camera_id = id_
        self.bn_camera_id.poke()

    def _camera_alive_changed(self) -> None:
        camera = self.bn_camera.get()
        assert camera is not None

        if camera.bn_alive.get() is False:
            self.remove_current_camera()

    def remove_current_camera(self, _poke_current_camera_id: bool = True) -> None:
        camera = self.bn_camera.get()
        if camera is None: return

        assert self._camera_alive_changed_conn is not None
        assert self._camera_alive_changed_conn.status is EventConnection.Status.CONNECTED

        self._camera_alive_changed_conn.disconnect()
        self._camera_alive_changed_conn = None

        camera.destroy()

        self._camera_id = None
        self.bn_camera.set(None)

        if _poke_current_camera_id:
            self.bn_camera_id.poke()

    def destroy(self) -> None:
        self.remove_current_camera(_poke_current_camera_id=False)
        self._harvester.reset()
        super().destroy()


class GenicamCamera(Camera):
    def __init__(self, hacquirer: harvesters.ImageAcquirer) -> None:
        self._hacquirer = hacquirer
        self.bn_alive = VariableBindable(False)

        try:
            hacquirer.start_acquisition(run_in_background=True)
        except genicam.gentl.IoException as e:
            raise ValueError('Camera failed to open.') from e

        self.bn_alive.set(True)

    def capture(self) -> np.ndarray:
        with self._hacquirer.fetch_buffer() as buf:
            if not buf.payload.components:
                raise CameraCaptureError

            component = buf.payload.components[0]

            width, height, channels = component.width, component.height, int(component.num_components_per_pixel)
            x_padding = component.x_padding

            data = component.data
            data = np.lib.stride_tricks.as_strided(
                data,
                shape=(height, width * channels),
                strides=((width*channels + x_padding)*data.itemsize, data.itemsize),
                writeable=False,
            )

            data_format = component.data_format

            if data_format == 'Mono8':
                image = cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)
            elif data_format == 'Mono10':
                image = cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)
                image = (image/1023*255).astype(np.uint8)
            elif data_format == 'Mono12':
                image = cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)
                image = (image/4095*255).astype(np.uint8)
            elif data_format == 'RGB8':
                image = data.reshape(height, width, 3).copy()
            elif data_format == 'RGB10':
                image = data.reshape(height, width, 3)
                image = (image/1023*255).astype(np.uint8)
            elif data_format == 'RGB12':
                image = data.reshape(height, width, 3)
                image = (image/4095*255).astype(np.uint8)
            elif data_format == 'BGR8':
                image = cv2.cvtColor(
                    data.reshape(height, width, 3),
                    code=cv2.COLOR_BGR2RGB,
                )
            elif data_format == 'BGR10':
                image = cv2.cvtColor(
                    data.reshape(height, width, 3),
                    code=cv2.COLOR_BGR2RGB,
                )
                image = (image/1023*255).astype(np.uint8)
            elif data_format == 'BGR12':
                image = cv2.cvtColor(
                    data.reshape(height, width, 3),
                    code=cv2.COLOR_BGR2RGB,
                )
                image = (image/4095*255).astype(np.uint8)
            elif data_format in {'BayerGR8', 'BayerRG8', 'BayerBG8', 'BayerGB8'}:
                image = cv2.cvtColor(
                    data,
                    # OpenCV has a different Bayer pattern naming convention.
                    code={'BayerGR8': cv2.COLOR_BayerGB2RGB,
                          'BayerRG8': cv2.COLOR_BayerBG2RGB,
                          'BayerBG8': cv2.COLOR_BayerRG2RGB,
                          'BayerGB8': cv2.COLOR_BayerGR2RGB,
                    }[data_format]
                )
            elif data_format in {'BayerGR10', 'BayerRG10', 'BayerBG10', 'BayerGB10'}:
                image = cv2.cvtColor(
                    data,
                    # OpenCV has a different Bayer pattern naming convention.
                    code={'BayerGR10': cv2.COLOR_BayerGB2RGB,
                          'BayerRG10': cv2.COLOR_BayerBG2RGB,
                          'BayerBG10': cv2.COLOR_BayerRG2RGB,
                          'BayerGB10': cv2.COLOR_BayerGR2RGB,
                    }[data_format]
                )
                image = (image/1023*255).astype(np.uint8)
            elif data_format in {'BayerGR12', 'BayerRG12', 'BayerBG12', 'BayerGB12'}:
                image = cv2.cvtColor(
                    data,
                    # OpenCV has a different Bayer pattern naming convention.
                    code={'BayerGR12': cv2.COLOR_BayerGB2RGB,
                          'BayerRG12': cv2.COLOR_BayerBG2RGB,
                          'BayerBG12': cv2.COLOR_BayerRG2RGB,
                          'BayerGB12': cv2.COLOR_BayerGR2RGB,
                    }[data_format]
                )
                image = (image/4095*255).astype(np.uint8)
            else:
                raise CameraCaptureError('Unsupported pixel format {}'.format(data_format))

            return image

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        if not hasattr(self, '_hacquirer'): return

        width = self._hacquirer.remote_device.node_map.Width.value
        height = self._hacquirer.remote_device.node_map.Height.value
        return width, height

    def destroy(self) -> None:
        if not hasattr(self, '_hacquirer'): return
        self._hacquirer.stop_acquisition()
        self._hacquirer.destroy()
        del self._hacquirer
        self.bn_alive.set(False)
