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
