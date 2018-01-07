from abc import abstractmethod

from typing import Optional, Type, Mapping, Any, Iterable, TypeVar

T = TypeVar('T', bound='IView')


class IView:
    @abstractmethod
    def do_setup(self) -> None: pass

    @abstractmethod
    def setup(self) -> None: pass

    @abstractmethod
    def close(self) -> None: pass

    @abstractmethod
    def spawn(self, new_view: Type[T], child: bool = False, args: Optional[Iterable] = None,
              kwargs: Optional[Mapping[str, Any]] = None) -> T: pass

    @abstractmethod
    def fire_ignore_args(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def connect(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def disconnect(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def inline(self, event_name: str) -> None: pass

    @abstractmethod
    def destroy(self) -> None: pass

    # Properties

    @property
    @abstractmethod
    def hidden(self) -> bool: pass

    @hidden.setter
    @abstractmethod
    def hidden(self, value: bool) -> None: pass

    @property
    def destroyed(self) -> bool: pass