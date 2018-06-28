from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.sample_mvp_app.main_menu.iview import IMainView
from opendrop.utility.events import Event


class MainView(GtkWindowView, IMainView):
    class _Events(GtkWindowView._Events):
        def __init__(self):
            super().__init__()
            self.on_timer_button_clicked = Event()
            self.on_burger_button_clicked = Event()
            self.on_camera_button_clicked = Event()
            self.on_about_button_clicked = Event()

    def setup(self) -> None:
        # -- Build the UI --
        grid = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)

        self.window.add(grid)

        button1 = Gtk.Button(label='Timer example')
        button2 = Gtk.Button(label='Burger example')
        button3 = Gtk.Button(label='Camera example')
        button4 = Gtk.Button(label='About')

        button1.event_name = 'on_timer_button_clicked'
        button2.event_name = 'on_burger_button_clicked'
        button3.event_name = 'on_camera_button_clicked'
        button4.event_name = 'on_about_button_clicked'

        grid.attach(button1, 0, 0, 1, 1)
        grid.attach(button2, 0, 1, 1, 1)
        grid.attach(button3, 0, 2, 1, 1)
        grid.attach(button4, 0, 3, 1, 1)

        self.window.show_all()

        # About dialog
        about_dialog = Gtk.AboutDialog(
           program_name= 'Sample Application',
                version= '1.0.0',
                website= 'http://www.example.org',
               comments= 'Example application with sample code to demonstrate use.',
                authors=['John',
                         'Jane',
                         'Jackson',
                         'Jennifer'],
            documenters=['Wayne'],
            transient_for=self.window, modal=True
        )

        # -- Attach events --
        for button in (button1, button2, button3, button4):
            button.connect('clicked', self.on_buttonx_clicked)

        # -- Keep these widgets accessible --
        self.about_dialog = about_dialog

    def on_buttonx_clicked(self, button: Gtk.Button) -> None:
        getattr(self.events, button.event_name).fire()

    def show_about_dialog(self) -> None:
        response = self.about_dialog.run()

        if response == Gtk.ResponseType.DELETE_EVENT or response == Gtk.ResponseType.CANCEL:
            self.about_dialog.hide()
