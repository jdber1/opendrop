from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.mvp.View import View
from opendrop.sample_mvp_app.burger_example.iview import IBurgerExampleView
from opendrop.utility import data_binding
from opendrop.utility.events import Event


class BurgerExampleView(GtkWindowView, IBurgerExampleView):
    class _Events(View._Events):
        def __init__(self):
            super().__init__()
            self.on_order_button_clicked = Event()

    def setup(self) -> None:
        # -- Build the UI --
        body = Gtk.ListBox()
        self.window.add(body)

        # Cheese row
        row = Gtk.ListBoxRow(selectable=False)
        body.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)

        cheese_label = Gtk.Label('Slices of cheese:', xalign=0)
        cheese_slices_input = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=0, lower=0, upper=4, step_incr=1),
            numeric=True,
            digits=0,
            snap_to_ticks=True
        )

        hbox.pack_start(cheese_label, True, True, 0)
        hbox.pack_start(cheese_slices_input, True, True, 0)

        # Bacon row
        row = Gtk.ListBoxRow(selectable=False)
        body.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)

        bacon_label = Gtk.Label('Bacon:', xalign=0)
        bacon_input = Gtk.CheckButton()

        hbox.pack_start(bacon_label, True, True, 0)
        hbox.pack_start(bacon_input, False, True, 0)

        # Meal size row
        row = Gtk.ListBoxRow(selectable=False)
        body.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        
        meal_label = Gtk.Label('Meal size:', xalign=0)
        meal_size_input = Gtk.ComboBoxText()

        meal_size_input.set_active(0)

        hbox.pack_start(meal_label, True, True, 0)
        hbox.pack_start(meal_size_input, True, True, 0)

        row = Gtk.ListBoxRow(selectable=False)
        body.add(row)

        order_button = Gtk.Button(label='Place Order')
        row.add(order_button)

        self.window.show_all()

        # -- Attach events --
        cheese_slices_input.connect(
            'value-changed', lambda w: data_binding.poke(self, BurgerExampleView.cheese_slices))
        bacon_input.connect(
            'toggled', lambda w: data_binding.poke(self, BurgerExampleView.bacon))
        meal_size_input.connect(
            'changed', lambda w: data_binding.poke(self, BurgerExampleView.meal_size))

        order_button.connect('clicked', lambda *_: self.events.on_order_button_clicked.fire())

        # -- Keep these widgets accessible --
        self.cheese_input = cheese_slices_input
        self.bacon_input  = bacon_input
        self.meal_input   = meal_size_input

        self.order_button = order_button

    def add_meal_size(self, display: str) -> None:
        self.meal_input.append(id=display, text=display)

    @data_binding.property
    def cheese_slices(self) -> int:
        return self.cheese_input.props.value

    @cheese_slices.setter
    def cheese_slices(self, value: int) -> None:
        self.cheese_input.props.value = value

    @data_binding.property
    def bacon(self) -> bool:
        return self.bacon_input.props.active

    @bacon.setter
    def bacon(self, value: bool) -> None:
        self.bacon_input.props.active = value

    @data_binding.property
    def meal_size(self) -> str:
        return self.meal_input.props.active_id

    @meal_size.setter
    def meal_size(self, value: str) -> None:
        self.meal_input.props.active_id = value

    order_cost = data_binding.property()

    @order_cost.setter
    def order_cost(self, cost: float) -> None:
        self.order_button.props.label = 'Place order (${0:.2f})'.format(cost)

    def show_order_confirmation(self, total_cost: float) -> None:
        # Order confirmation dialog
        order_confirmation_dialog = Gtk.MessageDialog(
            self.window, 0,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            'Burger order confirmation',
            modal=True
        )

        order_confirmation_dialog.format_secondary_markup('Total cost: ${0:.2f}'.format(total_cost))

        order_confirmation_dialog.show()

        def handle_response(*args):
            order_confirmation_dialog.destroy()

        order_confirmation_dialog.connect('response', handle_response)
