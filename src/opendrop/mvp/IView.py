from abc import abstractmethod

from typing import Optional, Type, Iterable


class IView:
    @abstractmethod
    def close(self, next_view: Optional[Type['IView']] = None) -> None: pass

    @abstractmethod
    def spawn(self, new_view: Type['IView'], modal: bool = False) -> None: pass

    @abstractmethod
    def fire_ignore_args(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def connect(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def disconnect(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def destroy(self) -> None: pass
