# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import pkg_resources
from gi.repository import Gtk, GdkPixbuf, Gio, GLib, Gdk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.app.services.app import OpendropService

main_menu_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@main_menu_cs.view()
class MainMenuView(View['MainMenuPresenter', Gtk.Widget]):
    OPENDROP_LOGO = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/logo_wide.png').read()
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
            default_width=400,
            default_height=240,
        )

        body = Gtk.Grid(row_spacing=15, column_spacing=40)
        self._window.add(body)

        body.get_style_context().add_class('body')
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes("""
            .body {
                background: white;
            }
            """, encoding='utf-8'))
        body.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        logo_image_pixbuf = self.OPENDROP_LOGO.scale_simple(
            dest_width=240,
            dest_height=240 / self.OPENDROP_LOGO.props.width * self.OPENDROP_LOGO.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        logo = Gtk.Image(pixbuf=logo_image_pixbuf, margin=20, hexpand=True)
        body.attach(logo, 0, 0, 2, 1)

        ift_btn = Gtk.Button(relief=Gtk.ReliefStyle.NONE, width_request=120, hexpand=True, vexpand=True, halign=Gtk.Align.END, valign=Gtk.Align.START)
        body.attach(ift_btn, 0, 1, 1, 1)

        ift_btn_inner = Gtk.Grid(hexpand=True, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, row_spacing=12, margin_top=4,
                                 margin_bottom=4)
        ift_btn.add(ift_btn_inner)

        ift_btn_image_pixbuf = self.IFT_BUTTON_IMAGE.scale_simple(
            dest_width=48,
            dest_height=48 / self.IFT_BUTTON_IMAGE.props.width * self.IFT_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )

        ift_btn_image = Gtk.Image(pixbuf=ift_btn_image_pixbuf, valign=Gtk.Align.CENTER)
        ift_btn_inner.attach(ift_btn_image, 0, 0, 1, 1)

        ift_btn_lbl = Gtk.Label(
            label='Interfacial Tension',
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )
        ift_btn_inner.attach(ift_btn_lbl, 0, 1, 1, 1)

        conan_btn = Gtk.Button(relief=Gtk.ReliefStyle.NONE, width_request=120, halign=Gtk.Align.START, valign=Gtk.Align.START)

        conan_btn_inner = Gtk.Grid(hexpand=True, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, row_spacing=12, margin_top=4,
                                   margin_bottom=4)
        conan_btn.add(conan_btn_inner)

        conan_btn_image_pixbuf = self.CONAN_BUTTON_IMAGE.scale_simple(
            dest_width=48,
            dest_height=48 / self.CONAN_BUTTON_IMAGE.props.width * self.CONAN_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        body.attach(conan_btn, 1, 1, 1, 1)

        conan_btn_image = Gtk.Image(pixbuf=conan_btn_image_pixbuf)
        conan_btn_inner.attach(conan_btn_image, 0, 0, 1, 1)

        conan_btn_lbl = Gtk.Label(
            label='Contact Angle',
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )
        conan_btn_inner.attach(conan_btn_lbl, 0, 1, 1, 1)

        ift_btn.connect('clicked', lambda *_: self.presenter.launch_ift())
        conan_btn.connect('clicked', lambda *_: self.presenter.launch_conan())

        self._window.connect('delete-event', self._hdl_window_delete_event)

        self._window.foreach(Gtk.Widget.show_all)

        return self._window

    def _hdl_window_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
        self.presenter.exit()
        return True

    def _do_destroy(self) -> None:
        self._window.destroy()


@main_menu_cs.presenter(options=['model'])
class MainMenuPresenter(Presenter['MainMenuView']):
    def _do_init(self, model: OpendropService):
        self._model = model

    def launch_ift(self) -> None:
        self._model.goto_ift()

    def launch_conan(self) -> None:
        self._model.goto_conan()

    def exit(self) -> None:
        self._model.quit()
