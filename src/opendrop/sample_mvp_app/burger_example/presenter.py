from typing import Any

from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.burger_example.iview import IBurgerExampleView
from opendrop.sample_mvp_app.main_menu.model import BurgerOrder
from opendrop.utility.events import handler


class BurgerExamplePresenter(Presenter[BurgerOrder, IBurgerExampleView]):
    def setup(self) -> None:
        self.cache = {}

        for meal_size in self.model.MealSizeType:
            self.view.add_meal_size(meal_size.display)

        # Sync the view with the existing data in model
        for name, value in self.model.order.items():
            self.handle_model_order_changed(name, value)

    @handler('view', 'on_order_changed')
    def handle_view_order_changed(self, name: str, value: Any) -> None:
        if self.cache[name] == value:
            return

        self.cache[name] = value

        self.model.edit_order(name, value)

    @handler('model', 'on_order_changed')
    def handle_model_order_changed(self, name: str, value: Any) -> None:
        if name in self.cache and self.cache[name] == value:
            return

        self.cache[name] = value

        self.view.edit_order(name, value)

    @handler('model', 'on_order_cost_changed')
    def handle_model_order_cost_changed(self) -> None:
        self.view.update_display_cost(self.model.order_cost)

    @handler('view', 'on_order_button_clicked')
    def handle_order_button_clicked(self) -> None:
        self.view.show_order_confirmation(self.model.order_cost)

    @handler('model', 'on_order_cost_changed')
    def handle_cost_changed(self) -> None:
        self.view.update_display_cost(self.model.order_cost)
