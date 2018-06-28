from opendrop.mvp.Presenter import Presenter

from opendrop.utility import data_binding

from .view import BurgerExampleView
from .model import BurgerOrder


class BurgerExamplePresenter(Presenter[BurgerOrder, BurgerExampleView]):
    def setup(self) -> None:
        for meal_size in self.model.MealSizeType:
            self.view.add_meal_size(meal_size.display)

        routes = [
            *data_binding.Route.both(BurgerOrder.order_cost, BurgerExampleView.order_cost),
            *data_binding.Route.both(BurgerOrder.cheese_slices, BurgerExampleView.cheese_slices),
            *data_binding.Route.both(BurgerOrder.bacon, BurgerExampleView.bacon),
            *data_binding.Route.both(BurgerOrder.meal_size, BurgerExampleView.meal_size,
                                     to_b=lambda m: m.display,
                                     to_a=lambda s: BurgerOrder.MealSizeType.from_display_string(s))
        ]

        data_binding.bind(self.model, self.view, routes=routes)
        data_binding.poke(self.model)

        # Connect event handlers
        self.view.events.on_order_button_clicked.connect(self.handle_order_button_clicked)

    def handle_order_button_clicked(self) -> None:
        self.view.show_order_confirmation(self.model.order_cost)
