from abc import abstractmethod
from typing import Optional

from opendrop.mvp.IView import IView


class ITimerExampleView(IView):
    @abstractmethod
    def get_timer_duration(self) -> int: pass

    @abstractmethod
    def set_timer_countdown_mode(self, value: bool) -> None: pass

    @abstractmethod
    def set_timer_countdown_value(self, value: Optional[int]) -> None: pass