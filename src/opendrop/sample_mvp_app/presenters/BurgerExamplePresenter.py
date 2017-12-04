from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.SampleAppModel import SampleAppModel

from opendrop.sample_mvp_app.presenters.iviews.IBurgerExampleView import IBurgerExampleView


class BurgerExamplePresenter(Presenter[SampleAppModel, IBurgerExampleView]):
    def setup(self) -> None:
        self.handle_order_changed()

    @handles('on_order_button_clicked')
    def handle_order_button_clicked(self) -> None:
        order = self.view.get_order()
        order_cost = self.model.burger_cost_calculator.calculate_order_cost(order)

        self.view.show_order_confirmation(order_cost)

    @handles('on_order_changed')
    def handle_order_changed(self) -> None:
        order = self.view.get_order()
        order_cost = self.model.burger_cost_calculator.calculate_order_cost(order)

        self.view.update_display_cost(order_cost)
