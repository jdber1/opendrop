from typing import Any, Mapping

from opendrop.app.presenters.IBurgerExampleView import IBurgerExampleView
from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter


class BurgerExamplePresenter(Presenter[Any, IBurgerExampleView]):
    BASE_COST = 4.00  # type: float

    MEAL_SIZE_PRICES = {
        'Small': 0.00,
        'Medium': 1.00,
        'Large': 1.50,
        'Supersize™': 1.90
    }  # type: Mapping[str, float]

    BACON_PRICE = 1.95  # type: float

    CHEESE_PRICE = 0.50  # type: float

    def setup(self):
        self.handle_order_changed()

    @handles('on_order_button_clicked')
    def handle_order_button_clicked(self) -> None:
        order = self.view.get_order()
        order_cost = self.calculate_order_cost(order)

        self.view.show_order_confirmation(order_cost)

    @handles('on_order_changed')
    def handle_order_changed(self) -> None:
        order = self.view.get_order()
        order_cost = self.calculate_order_cost(order)

        self.view.set_display_cost(order_cost)

    def calculate_order_cost(self, order: Mapping[str, Any]) -> float:
        order_cost = self.BASE_COST  # type: float

        order_cost += order['cheese_slices'] * self.CHEESE_PRICE
        order_cost += order['bacon'] * self.BACON_PRICE
        order_cost += self.MEAL_SIZE_PRICES[order['meal_size']]

        return order_cost
