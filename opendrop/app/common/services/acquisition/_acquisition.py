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


from enum import Enum
from typing import Optional, Tuple, Sequence

from ._acquirer import ImageAcquirer, InputImage, LocalStorageAcquirer, USBCameraAcquirer
from opendrop.utility.bindable import AccessorBindable


class ImageAcquisitionService:
    def __init__(self) -> None:
        self._acquirer = None  # type: Optional[ImageAcquirer]

        self.bn_acquirer = AccessorBindable(
            getter=self._get_acquirer,
        )

    def get_acquirer_type(self) -> Optional['AcquirerType']:
        acquirer = self._acquirer
        if acquirer is None:
            return None

        if isinstance(acquirer, LocalStorageAcquirer):
            return AcquirerType.LOCAL_STORAGE
        elif isinstance(acquirer, USBCameraAcquirer):
            return AcquirerType.USB_CAMERA
        else:
            raise ValueError(
                "Unknown acquirer '{}'"
                .format(acquirer)
            )

    def use_acquirer_type(self, acquirer_type: Optional['AcquirerType']) -> None:
        if acquirer_type is None:
            self._set_acquirer(None)
            return

        if acquirer_type is self.get_acquirer_type():
            return

        if acquirer_type is AcquirerType.LOCAL_STORAGE:
            new_acquirer = LocalStorageAcquirer()
        elif acquirer_type is AcquirerType.USB_CAMERA:
            new_acquirer = USBCameraAcquirer()
        else:
            raise ValueError(
                "Unknown acquirer type '{}'"
                .format(acquirer_type)
            )

        self._set_acquirer(new_acquirer)

    def acquire_images(self) -> Sequence[InputImage]:
        if self._acquirer is None:
            raise ValueError('No acquirer chosen yet')

        return self._acquirer.acquire_images()

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Return the size that the acquired images will have. If a sensible size cannot be determined, return None.
        """
        if self._acquirer is None:
            raise ValueError('No acquirer chosen yet')

        return self._acquirer.get_image_size_hint()

    def _get_acquirer(self) -> Optional[ImageAcquirer]:
        return self._acquirer

    def _set_acquirer(self, new_acquirer: Optional[ImageAcquirer]) -> None:
        old_acquirer = self._acquirer
        if old_acquirer is not None:
            old_acquirer.destroy()

        self._acquirer = new_acquirer
        self.bn_acquirer.poke()

    def destroy(self) -> None:
        if self._acquirer is not None:
            self._acquirer.destroy()


class AcquirerType(Enum):
    LOCAL_STORAGE = ('Local filesystem',)

    USB_CAMERA = ('USB Camera',)

    def __init__(self, display_name: str) -> None:
        self.display_name = display_name
