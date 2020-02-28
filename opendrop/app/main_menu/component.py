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
            default_width=500,
            default_height=330,
        )

        body = Gtk.Grid()
        self._window.add(body)

        logo_image_pixbuf = self.OPENDROP_LOGO.scale_simple(
            dest_width=140,
            dest_height=140 / self.OPENDROP_LOGO.props.width * self.OPENDROP_LOGO.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        logo = Gtk.Image(pixbuf=logo_image_pixbuf, margin=20, hexpand=True)
        body.attach(logo, 2, 0, 1, 1)

        body.attach(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL, visible=True), 1, 0, 1, 1)

        menu_items = Gtk.Box(
            vexpand=True,
            margin=0,
            spacing=0,
            halign=Gtk.Align.START,
            orientation=Gtk.Orientation.VERTICAL,
        )
        body.attach(menu_items, 0, 0, 1, 1)

        menu_items.get_style_context().add_class('menu-items')
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes("""
            .menu-items {
                background: whitesmoke;
            }
            """, encoding='utf-8'))

        menu_items.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        new_analysis_label = Gtk.Label(halign=Gtk.Align.START, margin_left=9, margin_top=6, margin_bottom=0)
        new_analysis_label.set_markup('<b>NEW ANALYSIS</b>')

        new_analysis_label.get_style_context().add_class('new-analysis-label')
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes("""
            .new-analysis-label {
                font-size: 11pt;
                color: dimgray;
            }
            """, encoding='utf-8'))

        new_analysis_label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        menu_items.pack_start(new_analysis_label, expand=False, fill=False, padding=4)
        menu_items.show_all()

        ift_btn = Gtk.Button(width_request=160, relief=Gtk.ReliefStyle.NONE)
        menu_items.pack_start(ift_btn, expand=False, fill=False, padding=0)

        ift_btn_inner = Gtk.Grid(hexpand=False, valign=Gtk.Align.CENTER, column_spacing=8, margin_top=4,
                                 margin_bottom=4)
        ift_btn.add(ift_btn_inner)

        ift_btn_image_pixbuf = self.IFT_BUTTON_IMAGE.scale_simple(
            dest_width=24,
            dest_height=24 / self.IFT_BUTTON_IMAGE.props.width * self.IFT_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )

        ift_btn_image = Gtk.Image(pixbuf=ift_btn_image_pixbuf, valign=Gtk.Align.CENTER)
        ift_btn_inner.attach(ift_btn_image, 0, 0, 1, 1)

        ift_btn_lbl = Gtk.Label(
            label='Interfacial Tension',
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
        )
        ift_btn_inner.attach(ift_btn_lbl, 1, 0, 1, 1)

        conan_btn = Gtk.Button(width_request=160, relief=Gtk.ReliefStyle.NONE)

        conan_btn_inner = Gtk.Grid(hexpand=False, valign=Gtk.Align.CENTER, column_spacing=8, margin_top=4,
                                   margin_bottom=4)
        conan_btn.add(conan_btn_inner)

        conan_btn_image_pixbuf = self.CONAN_BUTTON_IMAGE.scale_simple(
            dest_width=24,
            dest_height=24 / self.CONAN_BUTTON_IMAGE.props.width * self.CONAN_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR
        )
        menu_items.pack_start(conan_btn, expand=False, fill=False, padding=0)

        conan_btn_image = Gtk.Image(pixbuf=conan_btn_image_pixbuf)
        conan_btn_inner.attach(conan_btn_image, 0, 0, 1, 1)

        conan_btn_lbl = Gtk.Label(
            label='Contact Angle',
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
        )
        conan_btn_inner.attach(conan_btn_lbl, 1, 0, 1, 1)

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
    def _do_init(self, model: MainMenuModel):
        self._model = model

    def launch_ift(self) -> None:
        self._model.launch_ift()

    def launch_conan(self) -> None:
        self._model.launch_conan()

    def exit(self) -> None:
        self._model.exit()
