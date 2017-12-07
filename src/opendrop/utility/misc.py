import importlib
import pkgutil
from enum import Enum
from types import ModuleType
from typing import Union, Optional, Any


def recursive_load(pkg: Union[ModuleType, str]):
    pkg = importlib.import_module(pkg) if isinstance(pkg, str) else pkg

    enums = []

    if hasattr(pkg, '__path__'):
        for loader, name, is_pkg in pkgutil.walk_packages(pkg.__path__):
            full_name = pkg.__name__ + '.' + name

            child = importlib.import_module(full_name)

            if is_pkg:
                enums += recursive_load(child)

    return enums


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
