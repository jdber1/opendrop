from abc import abstractmethod
from typing import Any, Mapping

from opendrop.mvp.IView import IView


class IBurgerExampleView(IView):
    @abstractmethod
    def get_order(self) -> Mapping[str, Any]: pass

    @abstractmethod
    def set_display_cost(self, cost: float) -> None: pass

    @abstractmethod
    def show_order_confirmation(self, total_cost: float) -> None: pass