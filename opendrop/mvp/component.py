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
from collections import namedtuple
from typing import Any, Optional, Iterable, Callable, Tuple, Mapping, MutableSequence, TypeVar, MutableMapping, Generic

from opendrop.mvp.presenter import Presenter
from opendrop.mvp.view import View
from opendrop.utility.events import Event

ViewClassType = TypeVar('ViewClassType', bound=Callable[..., View])
PresenterClassType = TypeVar('PresenterClassType', bound=Callable[..., Presenter])

ComponentViewRepType = TypeVar('ComponentViewRepType')


T = TypeVar('T')


class ComponentSymbol(Generic[ComponentViewRepType]):
    def __init__(self) -> None:
        self._view_cls = None
        self._view_options = tuple()  # type: Tuple[str]

        self._presenter_cls = None  # type: Optional[Callable[..., Presenter]]
        self._presenter_options = tuple()  # type: Tuple[str]

    def factory(self, **options) -> 'ComponentFactory[ComponentViewRepType]':
        return ComponentFactory(self, options=options)

    def view(self, options: Iterable[str] = tuple()) -> Callable:
        def inner(view_cls: ViewClassType) -> ViewClassType:
            self._view_cls = view_cls
            self._view_options = tuple(options)

            return view_cls

        return inner

    def presenter(self, options: Iterable[str] = tuple()) -> Callable:
        def inner(presenter_cls: PresenterClassType) -> PresenterClassType:
            self._presenter_cls = presenter_cls
            self._presenter_options = tuple(options)

            return presenter_cls

        return inner


class ComponentFactory(Generic[ComponentViewRepType]):
    def __init__(self, csymbol: ComponentSymbol, options: Optional[Mapping[str, Any]] = None) -> None:
        self._csymbol = csymbol
        self._options = options or {}

    def create(self, view_env: Optional[MutableMapping] = None, presenter_env: Optional[MutableMapping] = None) \
            -> 'Component[ComponentViewRepType]':
        view_cls = self._csymbol._view_cls
        presenter_cls = self._csymbol._presenter_cls

        view_options, presenter_options = self._resolve_options(self._options)

        new_view = view_cls(env=view_env, options=view_options)
        new_presenter = presenter_cls(env=presenter_env, options=presenter_options)

        new_component = Component(view=new_view, presenter=new_presenter)

        return new_component

    def _resolve_options(self, options: Mapping[str, Any]) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
        view_option_keywords = self._csymbol._view_options
        presenter_option_keywords = self._csymbol._presenter_options
        view_options = {}
        presenter_options = {}

        for k, v in options.items():
            unknown_keyword = True

            if k in view_option_keywords:
                unknown_keyword = False
                view_options[k] = v

            if k in presenter_option_keywords:
                unknown_keyword = False
                presenter_options[k] = v

            if unknown_keyword:
                raise TypeError("Unexpected option '{}'".format(k))

        return view_options, presenter_options

    def fork(self, **options) -> 'ComponentFactory[ComponentViewRepType]':
        new_options = options
        new_options.update(self._options)

        return ComponentFactory(self._csymbol, options=new_options)


class Component(Generic[ComponentViewRepType]):
    ChildContainer = namedtuple('ChildContainer', ['component', 'on_destroyed_conn'])

    def __init__(self, view: View[Any, ComponentViewRepType], presenter: Presenter) -> None:
        self._view = view
        self._presenter = presenter

        self._children = []  # type: MutableSequence[Component.ChildContainer]

        self.on_destroyed = Event()
        self.is_destroyed = False

        self._presenter._component_hooks.component_destroy = self.destroy

        self._view._component_hooks.new_component = self._new_component_for_view
        self._view._component_hooks.remove_component = self._remove_component_for_view

        self._presenter._init(self._view)
        self.view_rep = self._view._init(self._presenter)  # type: ComponentViewRepType

    def new_component(self, cfactory: ComponentFactory[T]) -> 'Component[T]':
        new_child_view_env = self._view.extend_env()
        new_child_presenter_env = self._presenter.extend_env()

        new_child = cfactory.create(view_env=new_child_view_env, presenter_env=new_child_presenter_env)

        self._children.append(self.ChildContainer(
            component=new_child,
            on_destroyed_conn=new_child.on_destroyed.connect(self.remove_component)
        ))

        return new_child

    def remove_component(self, component: 'Component') -> None:
        for x in self._children:
            if x.component == component:
                child_container = x
                break
        else:
            raise ValueError('Component is not a child of this')

        self._children.remove(child_container)

        child_container.on_destroyed_conn.disconnect()
        child_component = child_container.component

        if not child_component.is_destroyed:
            child_component.destroy()

    def _new_component_for_view(self, cfactory: ComponentFactory[T]) -> Tuple[Any, T]:
        new_child = self.new_component(cfactory)

        return new_child, new_child.view_rep

    def _remove_component_for_view(self, component_id: Any) -> None:
        return self.remove_component(component_id)

    def destroy(self) -> None:
        for child_container in list(self._children):
            self.remove_component(child_container.component)

        self._presenter._destroy()
        self._view._destroy()

        self.is_destroyed = True
        self.on_destroyed.fire(self)
