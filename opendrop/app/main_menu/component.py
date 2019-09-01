import pkg_resources
from gi.repository import Gtk, GdkPixbuf, Gio, GLib, Gdk

from opendrop.mvp import ComponentSymbol, View, Presenter
from .model import MainMenuModel

main_menu_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@main_menu_cs.view()
class MainMenuView(View['MainMenuPresenter', Gtk.Widget]):
    OPENDROP_LOGO = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/logo_tall.png').read()
            )
        )
    )

    IFT_BUTTON_IMAGE = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/ift_btn.png').read()
            )
        )
    )

    CONAN_BUTTON_IMAGE = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/conan_btn.png').read()
            )
        )
    )

    def _do_init(self) -> Gtk.Widget:
        self._window = Gtk.Window(
            title='OpenDrop',
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        body = Gtk.Grid(
            valign=Gtk.Align.CENTER,
        )
        body.show()
        self._window.add(body)

        logo_image_pixbuf = self.OPENDROP_LOGO.scale_simple(
            dest_width=140,
            dest_height=140/self.OPENDROP_LOGO.props.width * self.OPENDROP_LOGO.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        logo = Gtk.Image(pixbuf=logo_image_pixbuf, margin=10)
        logo.show()
        body.attach(logo, 0, 0, 1, 1)

        body.attach(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL, visible=True), 1, 0, 1, 1)

        menu_items = Gtk.Box(
            hexpand=True,
            margin=10,
            spacing=10,
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
            orientation=Gtk.Orientation.VERTICAL,
        )
        menu_items.show()
        body.attach(menu_items, 2, 0, 1, 1)

        ift_btn = Gtk.Button(width_request=170)

        ift_btn_inner = Gtk.Grid(hexpand=False, vexpand=False, column_spacing=8)

        ift_btn_image_pixbuf = self.IFT_BUTTON_IMAGE.scale_simple(
            dest_width=32,
            dest_height=32/self.IFT_BUTTON_IMAGE.props.width * self.IFT_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )

        ift_btn_image = Gtk.Image(pixbuf=ift_btn_image_pixbuf)
        ift_btn_image.show()
        ift_btn_inner.attach(ift_btn_image, 0, 0, 1, 1)

        ift_btn_lbl = Gtk.Label(
            label='Interfacial Tension',
            hexpand=True,
            vexpand=True,
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
        )
        ift_btn_lbl.show()
        ift_btn_inner.attach(ift_btn_lbl, 1, 0, 1, 1)

        ift_btn_inner.show()
        ift_btn.add(ift_btn_inner)

        ift_btn.show()
        menu_items.pack_start(ift_btn, expand=True, fill=False, padding=0)

        conan_btn = Gtk.Button(width_request=170)

        conan_btn_inner = Gtk.Grid(hexpand=False, vexpand=False, column_spacing=8)

        conan_btn_image_pixbuf = self.CONAN_BUTTON_IMAGE.scale_simple(
            dest_width=32,
            dest_height=32/self.CONAN_BUTTON_IMAGE.props.width * self.CONAN_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        conan_btn_image = Gtk.Image(pixbuf=conan_btn_image_pixbuf)
        conan_btn_image.show()
        conan_btn_inner.attach(conan_btn_image, 0, 0, 1, 1)

        conan_btn_lbl = Gtk.Label(
            label='Contact Angle',
            hexpand=True,
            vexpand=True,
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
        )
        conan_btn_lbl.show()
        conan_btn_inner.attach(conan_btn_lbl, 1, 0, 1, 1)

        conan_btn_inner.show()
        conan_btn.add(conan_btn_inner)

        conan_btn.show()
        menu_items.pack_start(conan_btn, expand=True, fill=False, padding=0)

        ift_btn.connect('clicked', lambda *_: self.presenter.launch_ift())
        conan_btn.connect('clicked', lambda *_: self.presenter.launch_conan())

        self._window.connect('delete-event', self._hdl_window_delete_event)

        return self._window

    def _hdl_window_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
        self.presenter.exit()
        return True

    def _do_destroy(self) -> None:
        self._window.destroy()


@main_menu_cs.presenter(options=['model'])
class MainMenuPresenter(Presenter['MainMenuView']):
    def _do_init(self, model: MainMenuModel):
        self._model = model

    def launch_ift(self) -> None:
        self._model.launch_ift()

    def launch_conan(self) -> None:
        self._model.launch_conan()

    def exit(self) -> None:
        self._model.exit()
