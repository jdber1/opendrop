from opendrop.mvp.Presenter import Presenter
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM
from .model import BurgerOrder
from .view import BurgerExampleView


class BurgerExamplePresenter(Presenter[BurgerOrder, BurgerExampleView]):
    def setup(self) -> None:
        for meal_sz in self.model.MealSizeType:
            self.view.add_meal_size(meal_sz.display)

        # Bind bindables.
        self._data_binds = [
            Binding(src=self.model.bn_order_cost,    dst=self.view.bn_order_cost),
            Binding(src=self.model.bn_cheese_slices, dst=self.view.bn_cheese_slices),
            Binding(src=self.model.bn_bacon,         dst=self.view.bn_bacon),
            Binding(src=self.model.bn_meal_size,     dst=self.view.bn_meal_size,
                    mitm=AtomicBindingMITM(
                        to_src=BurgerOrder.MealSizeType.from_display,
                        to_dst=lambda meal_sz: meal_sz.display
                    )),
        ]

        # Connect event handlers.
        self._event_conns = [
            self.view.events.on_order_button_clicked.connect(self.hdl_order_button_clicked)
        ]

    def hdl_order_button_clicked(self) -> None:
        self.view.show_order_confirmation(self.model.order_cost)

    def teardown(self):
        for bind in self._data_binds:
            bind.unbind()

        for conn in self._event_conns:
            conn.disconnect()
