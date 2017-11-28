from typing import Optional

from gi.repository import Gtk

from opendrop.app.bases.GtkApplicationWindowView import GtkApplicationWindowView
from opendrop.app.presenters.ITimerExampleView import ITimerExampleView


class TimerExampleView(GtkApplicationWindowView, ITimerExampleView):
    def setup(self):
        listbox = Gtk.ListBox()
        self.window.add(listbox)

        row1 = Gtk.ListBoxRow(selectable=False)
        listbox.add(row1)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row1.add(hbox)

        timer_label = Gtk.Label('Timer:', xalign=0)
        timer_duration = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=10, lower=1, upper=60, step_incr=1),
            numeric=True,
            digits=0,
            snap_to_ticks=True
        )

        hbox.pack_start(timer_label, True, True, 0)
        hbox.pack_start(timer_duration, True, True, 0)

        row2 = Gtk.ListBoxRow()
        listbox.add(row2)

        start_button = Gtk.Button(label='Start timer')
        row2.add(start_button)

        self.window.show_all()

        # Attach events
        start_button.connect('clicked', self.on_start_button_clicked)

        # Keep these widgets accessible
        self.timer_duration = timer_duration
        self.start_button = start_button

    def on_start_button_clicked(self, button):
        self.fire('on_start_button_clicked')

    def get_timer_duration(self):
        return self.timer_duration.get_value()

    def set_timer_countdown_mode(self, value: bool) -> None:
        self.timer_duration.set_sensitive(not value)
        self.start_button.set_sensitive(not value)

    def set_timer_countdown_value(self, value: Optional[int]) -> None:
        if value:
            self.start_button.props.label = 'Remaining: {} s'.format(value)
        else:
            self.start_button.props.label = 'Start timer'
