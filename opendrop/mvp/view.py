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
from collections import ChainMap
from typing import Mapping, Optional, Any, MutableMapping, TypeVar, Generic, Callable, Tuple

from opendrop.mvp.typing import ComponentFactory
from opendrop.mvp.presenter import Presenter

PresenterType = TypeVar('PresenterType', bound=Presenter)
RepType = TypeVar('RepType')

T = TypeVar('T')


class View(Generic[PresenterType, RepType]):
    class ComponentHooks:
        new_component = None  # type: Callable
        remove_component = None  # type: Callable

    def __init__(self, *, env: Optional[MutableMapping] = None, options: Optional[Mapping[str, Any]] = None) -> None:
        self._component_hooks = self.ComponentHooks()
        self._options = options or {}  # type: Mapping[str, Any]

        self.env = env or {}  # type: MutableMapping
        self.presenter = None  # type: Optional[PresenterType]

    def _init(self, presenter: PresenterType) -> Any:
        self.presenter = presenter
        return self._do_init(**self._options)

    def _destroy(self) -> None:
        self._do_destroy()

    def new_component(self, cfactory: ComponentFactory[T]) -> Tuple[Any, T]:
        return self._component_hooks.new_component(cfactory)

    def remove_component(self, component_id: Any) -> None:
        return self._component_hooks.remove_component(component_id)

    def extend_env(self) -> MutableMapping:
        return ChainMap({}, self.env)

    def _do_init(self, **options) -> RepType:
        pass

    def _do_destroy(self) -> None:
        pass
