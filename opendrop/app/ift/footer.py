from gi.repository import Gtk, Gdk

from opendrop.component.gtk_widget_view import GtkWidgetView


class FooterView(GtkWidgetView[Gtk.Box]):
    STYLE = '''
    .footer-nav-btn {
         min-height: 0px;
         min-width: 60px;
         padding: 8px 4px 8px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        # Placeholder widgets

        self.widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=10)
        back_btn = Gtk.Button('< Back')
        back_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_start(back_btn, expand=False, fill=False, padding=0)

        next_btn = Gtk.Button('Next >')
        next_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_end(next_btn, expand=False, fill=False, padding=0)
        self.widget.show_all()
