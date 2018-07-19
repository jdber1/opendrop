from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.mvp.View import View
from opendrop.sample_mvp_app.burger_example.iview import IBurgerExampleView
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter
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

        order_button.connect('clicked', lambda *_: self.events.on_order_button_clicked.fire())

        # -- Keep these widgets accessible --
        self.cheese_input = cheese_slices_input
        self.bacon_input  = bacon_input
        self.meal_size_input   = meal_size_input

        self.order_button = order_button

        self.bn_cheese_slices = AtomicBindableAdapter(
            getter=self.cheese_input.get_value,
            setter=self.cheese_input.set_value
        )
        self.bn_bacon = AtomicBindableAdapter(
            getter=self.bacon_input.get_active,
            setter=self.bacon_input.set_active
        )
        self.bn_meal_size = AtomicBindableAdapter(
            getter=self.meal_size_input.get_active_id,
            setter=self.meal_size_input.set_active_id
        )
        self.bn_order_cost = AtomicBindableAdapter(
            setter=lambda cost: self.order_button.set_label('Place order (${0:.2f})'.format(cost))
        )

        # -- Attach events --
        cheese_slices_input.connect(
            'value-changed', lambda w: self.bn_cheese_slices.poke())
        bacon_input.connect(
            'toggled', lambda w: self.bn_bacon.poke())
        meal_size_input.connect(
            'changed', lambda w: self.bn_meal_size.poke())

    def add_meal_size(self, display: str) -> None:
        self.meal_size_input.append(id=display, text=display)

    @AtomicBindable.property_adapter
    def cheese_slices(self) -> int:
        return self.bn_cheese_slices

    @AtomicBindable.property_adapter
    def bacon(self) -> int:
        return self.bn_bacon

    @AtomicBindable.property_adapter
    def meal_size(self) -> int:
        return self.bn_meal_size

    @AtomicBindable.property_adapter
    def meal_size(self) -> int:
        return self.bn_order_cost

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
