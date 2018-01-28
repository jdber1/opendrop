from functools import partial
from typing import Any

from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.sample_mvp_app.burger_example.iview import IBurgerExampleView


class BurgerExampleView(GtkWindowView, IBurgerExampleView):
    def setup(self) -> None:
        # -- Build the UI --
        listbox = Gtk.ListBox()
        self.window.add(listbox)

        # Cheese row
        row = Gtk.ListBoxRow(selectable=False)
        listbox.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)

        cheese_label = Gtk.Label('Slices of cheese:', xalign=0)
        cheese_input = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=0, lower=0, upper=4, step_incr=1),
            numeric=True,
            digits=0,
            snap_to_ticks=True
        )

        hbox.pack_start(cheese_label, True, True, 0)
        hbox.pack_start(cheese_input, True, True, 0)

        # Bacon row
        row = Gtk.ListBoxRow(selectable=False)
        listbox.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)

        bacon_label = Gtk.Label('Bacon:', xalign=0)
        bacon_input = Gtk.CheckButton()

        hbox.pack_start(bacon_label, True, True, 0)
        hbox.pack_start(bacon_input, False, True, 0)

        # Meal size row
        row = Gtk.ListBoxRow(selectable=False)
        listbox.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        
        meal_label = Gtk.Label('Meal size:', xalign=0)
        meal_input = Gtk.ComboBoxText()

        meal_input.set_active(0)

        hbox.pack_start(meal_label, True, True, 0)
        hbox.pack_start(meal_input, True, True, 0)

        row = Gtk.ListBoxRow(selectable=False)
        listbox.add(row)

        order_button = Gtk.Button(label='Place Order')
        row.add(order_button)

        self.window.show_all()

        # -- Attach events --
        cheese_input.connect(
            'value-changed', lambda w: self._on_order_changed('cheese_slices', cheese_input.get_value_as_int()))
        bacon_input.connect(
            'toggled', lambda w: self._on_order_changed('bacon', bacon_input.get_active()))
        meal_input.connect(
            'changed', lambda w: self._on_order_changed('meal_size', meal_input.get_active_text()))

        order_button.connect('clicked', self.events.on_order_button_clicked.fire_ignore_args)

        # -- Keep these widgets accessible --
        self.cheese_input = cheese_input
        self.bacon_input  = bacon_input
        self.meal_input   = meal_input

        self.order_button = order_button

    def _on_order_changed(self, name: str, value: Any) -> None:
        self.events.on_order_changed.fire(name, value)

    def add_meal_size(self, display: str) -> None:
        self.meal_input.append(id=display, text=display)

    def edit_order(self, name: str, value: Any) -> None:
        if name == 'cheese_slices':
            self.cheese_input.props.value = int(value)
        elif name == 'bacon':
            self.bacon_input.props.active = bool(value)
        elif name == 'meal_size':
            self.meal_input.props.active_id = str(value)

    def update_display_cost(self, cost: float) -> None:
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
