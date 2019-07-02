from collections import ChainMap
from typing import Mapping, Optional, Any, MutableMapping, TypeVar, Generic, Callable

ViewType = TypeVar('ViewType')


class Presenter(Generic[ViewType]):
    class ComponentHooks:
        component_destroy = None  # type: Callable

    def __init__(self, *, env: Optional[MutableMapping] = None, options: Optional[Mapping[str, Any]] = None) -> None:
        self._component_hooks = self.ComponentHooks()
        self._options = options or {}  # type: Mapping[str, Any]

        self.env = env or {}  # type: MutableMapping
        self.view = None  # type: ViewType

    def _init(self, view: ViewType) -> None:
        self.view = view
        self._do_init(**self._options)

    def _destroy(self) -> None:
        self._do_destroy()

    def component_destroy(self) -> None:
        assert self._component_hooks.component_destroy is not None
        self._component_hooks.component_destroy()

    def extend_env(self) -> MutableMapping:
        return ChainMap({}, self.env)

    def _do_init(self, **options) -> None:
        pass

    def _do_destroy(self) -> None:
        pass
