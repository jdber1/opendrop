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
import itertools
from typing import Callable, TypeVar

from opendrop.utility.bindable.bindable import Bindable

_T = TypeVar('_T')


class _FunctionApplierBindable(Bindable[_T]):
    def __init__(self, function: Callable[..., _T], *bn_args: Bindable, **bn_kwargs: Bindable) -> None:
        super().__init__()

        self._function = function
        self._bn_args = bn_args
        self._bn_kwargs = bn_kwargs

        for bn_arg in itertools.chain(bn_args, bn_kwargs.values()):
            bn_arg.on_changed.connect(self._arguments_changed)

    def _arguments_changed(self):
        self.on_changed.fire()

    def _get_value(self) -> _T:
        args = [bn.get() for bn in self._bn_args]
        kwargs = {key: bn.get() for key, bn in self._bn_kwargs.items()}

        return self._function(*args, **kwargs)

    def _set_value(self, new_value: _T) -> None:
        raise NotImplementedError("can't set bindable result of apply()")


apply = _FunctionApplierBindable
