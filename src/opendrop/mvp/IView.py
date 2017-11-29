from abc import abstractmethod

from typing import Callable, Optional, Type


class IView:
    @abstractmethod
    def close(self, next_view: Optional[Type['IView']] = None) -> None: pass

    @abstractmethod
    def spawn(self, new_view: Type['IView'], modal: bool = False) -> None: pass

    @abstractmethod
    def fire(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def fire_ignore_args(self, event_name: str, *args, **kwargs) -> None: pass

    @abstractmethod
    def connect(self, event_name: str, handler: Callable[..., None], *args, **kwargs) -> None: pass

    @abstractmethod
    def disconnect(self, event_name: str, handler: Callable[..., None]) -> None: pass

    @abstractmethod
    def destroy(self) -> None: pass
