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


from pathlib import Path
from typing import Union, Sequence, MutableSequence

import cv2
import numpy as np

from opendrop.utility.bindable import VariableBindable
from .image_sequence import ImageSequenceAcquirer


class LocalStorageAcquirer(ImageSequenceAcquirer):
    IS_REPLICATED = True

    def __init__(self) -> None:
        super().__init__()
        self.bn_last_loaded_paths = VariableBindable(tuple())  # type: VariableBindable[Sequence[Path]]

    def load_image_paths(self, image_paths: Sequence[Union[Path, str]]) -> None:
        # Sort image paths in lexicographic order, and ignore paths to directories.
        image_paths = sorted([p for p in map(Path, image_paths) if not p.is_dir()])

        images: MutableSequence[np.ndarray] = []
        for image_path in image_paths:
            # Load in grayscale to save memory.
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Failed to load image from '{image_path}'")

            image.flags.writeable = False

            images.append(image)

        self.bn_images.set(images)
        self.bn_last_loaded_paths.set(tuple(image_paths))
