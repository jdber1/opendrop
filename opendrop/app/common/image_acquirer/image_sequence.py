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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from typing import Sequence, Tuple, Optional

import numpy as np

from opendrop.utility.bindable import Bindable, BoxBindable
from .base import ImageAcquirer, InputImage


class ImageSequenceAcquirer(ImageAcquirer):
    IS_REPLICATED = False

    def __init__(self) -> None:
        self.bn_images = BoxBindable(tuple())  # type: Bindable[Sequence[np.ndarray]]

        self.bn_frame_interval = BoxBindable(None)  # type: Bindable[Optional[int]]

    def acquire_images(self) -> Sequence[InputImage]:
        images = self.bn_images.get()
        if len(images) == 0:
            raise ValueError("'_images' can't be empty")

        frame_interval = self.bn_frame_interval.get()
        if frame_interval is None or frame_interval <= 0:
            if len(images) == 1:
                # Since only one image, we don't care about the frame_interval.
                frame_interval = 0
            else:
                raise ValueError(
                    "'frame_interval' must be > 0 and not None, currently: '{}'"
                    .format(frame_interval)
                )

        input_images = []

        for i, img in enumerate(images):
            input_image = _BaseImageSequenceInputImage(
                image=img,
                timestamp=i * frame_interval
            )
            input_image.is_replicated = self.IS_REPLICATED
            input_images.append(input_image)

        return input_images

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        images = self.bn_images.get()
        if images is None or len(images) == 0:
            return None

        first_image = images[0]
        return first_image.shape[1::-1]


class _BaseImageSequenceInputImage(InputImage):
    def __init__(self, image: np.ndarray, timestamp: float) -> None:
        self._image = image
        self._timestamp = timestamp

    async def read(self) -> Tuple[np.ndarray, float]:
        return self._image, self._timestamp
