import importlib
import inspect
import pkgutil
from enum import Enum
from types import ModuleType
from typing import Union, Optional, Any, Type, List, Iterable, TypeVar

T = TypeVar('T')


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


# No longer used by anything, probably delete in the future
class EnumBuilder:
    def __init__(self, value: str, type: Optional[type] = None) -> None:
        self._value = value
        self._type = type
        self._names = {}

    def add(self, name: str, val: Any) -> None:
        self._names[name] = val

    def remove(self, name: str) -> None:
        del self._names[name]

    def build(self):
        return Enum(self._value, names=self._names, type=self._type)
