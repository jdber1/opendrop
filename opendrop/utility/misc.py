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


import importlib
import inspect
import pkgutil
import shutil
from pathlib import Path
from types import ModuleType
from typing import Union, Type, List, Iterable, TypeVar

import numpy as np


T = TypeVar('T')


def rotation_mat2d(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array(
        [[c, -s],
         [s,  c]]
    )


def recursive_load(pkg: Union[ModuleType, str]) -> List[ModuleType]:
    pkg = importlib.import_module(pkg) if isinstance(pkg, str) else pkg  # type: ModuleType

    loaded_modules = [pkg]  # type: List[ModuleType]

    if hasattr(pkg, '__path__'):
        for loader, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
            full_name = pkg.__name__ + '.' + name
            child = importlib.import_module(full_name)
            loaded_modules += recursive_load(child)

    return loaded_modules


def get_classes_in_modules(m: Union[Iterable[ModuleType], ModuleType], cls: T) -> List[T]:
    clses = []  # type: List[Type]

    if isinstance(m, Iterable):
        for v in m:
            clses += get_classes_in_modules(v, cls)

        return clses

    for name in dir(m):
        attr = getattr(m, name)

        if inspect.isclass(attr) and issubclass(attr, cls) and attr.__module__ == m.__name__:
            clses.append(attr)

    return clses


def clamp(x: float, lower: float, upper: float) -> float:
    """Return `lower` if `x < lower`,
              `upper` if `x > upper` and
              `x`     if `lower < x < upper`
    """
    return max(min(x, upper), lower)


def clear_directory_contents(path: Path) -> None:
    if not path.is_dir():
        return

    for child_path in path.iterdir():
        if child_path.is_file():
            child_path.unlink()
        elif child_path.is_dir():
            shutil.rmtree(str(child_path))
