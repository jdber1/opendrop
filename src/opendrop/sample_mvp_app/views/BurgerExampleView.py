from functools import partial
from typing import Mapping, Any

from gi.repository import Gtk

from opendrop.sample_mvp_app.bases.GtkApplicationWindowView import GtkApplicationWindowView

from opendrop.sample_mvp_app.presenters.IBurgerExampleView import IBurgerExampleView


class BurgerExampleView(GtkApplicationWindowView, IBurgerExampleView):
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

        for size in ('Small', 'Medium', 'Large', 'Supersize™'):
            meal_input.append(None, size)

        meal_input.set_active(0)

        hbox.pack_start(meal_label, True, True, 0)
        hbox.pack_start(meal_input, True, True, 0)

        row = Gtk.ListBoxRow(selectable=False)
        listbox.add(row)

        order_button = Gtk.Button(label='Place Order')
        row.add(order_button)

        self.window.show_all()

        # Order confirmation dialog
        order_confirmation_dialog = Gtk.MessageDialog(
            self.window, 0,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            'Burger order confirmation',
            modal=True
        )

        # -- Attach events --
        cheese_input.connect('value-changed', partial(self.fire_ignore_args, 'on_order_changed'))
        bacon_input .connect('toggled'      , partial(self.fire_ignore_args, 'on_order_changed'))
        meal_input  .connect('changed'      , partial(self.fire_ignore_args, 'on_order_changed'))

        order_button.connect('clicked', partial(self.fire_ignore_args, 'on_order_button_clicked'))

        # -- Keep these widgets accessible --
        self.cheese_input = cheese_input
        self.bacon_input  = bacon_input
        self.meal_input   = meal_input

        self.order_button = order_button

        self.order_confirmation_dialog = order_confirmation_dialog

    def get_order(self) -> Mapping[str, Any]:
        order = {
            'cheese_slices': self.cheese_input.get_value_as_int(),
            'bacon'        : self.bacon_input .get_active(),
            'meal_size'    : self.meal_input  .get_active_text()
        }

        return order

    def update_display_cost(self, cost: float) -> None:
        self.order_button.props.label = 'Place order (${0:.2f})'.format(cost)

    def show_order_confirmation(self, total_cost: float) -> None:
        self.order_confirmation_dialog.format_secondary_markup('Total cost: ${0:.2f}'.format(total_cost))

        resp = self.order_confirmation_dialog.run()

        self.order_confirmation_dialog.hide()
