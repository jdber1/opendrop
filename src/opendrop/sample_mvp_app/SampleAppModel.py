from typing import Any, Mapping

from opendrop.mvp.Model import Model


class SampleAppModel(Model):
    def __init__(self):
        self.burger_cost_calculator = BurgerCostCalculator()  # type: BurgerCostCalculator


class BurgerCostCalculator:
    BASE_COST = 4.00  # type: float

    MEAL_SIZE_PRICES = {
        'Small': 0.00,
        'Medium': 1.00,
        'Large': 1.50,
        'Supersize™': 1.90
    }  # type: Mapping[str, float]

    BACON_PRICE = 1.95  # type: float

    CHEESE_PRICE = 0.50  # type: float

    def calculate_order_cost(self, order: Mapping[str, Any]) -> float:
        order_cost = self.BASE_COST  # type: float

        order_cost += order['cheese_slices'] * self.CHEESE_PRICE
        order_cost += order['bacon'] * self.BACON_PRICE
        order_cost += self.MEAL_SIZE_PRICES[order['meal_size']]

        return order_cost
