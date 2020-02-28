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


from typing import MutableMapping, Mapping, Any

from gi.repository import Gtk, Gdk, GObject

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.typing import Bindable

sidebar_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@sidebar_cs.view(options=['titles'])
class SidebarView(View['SidebarPresenter', Gtk.Widget]):
    STYLE = '''
    .wizard-sidebar {
        background-color: GAINSBORO;
        border-right: 1px solid SILVER;
        padding: 15px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class _SidebarTitleLabel(Gtk.Label):
        def __init__(self, label: str, **options) -> None:
            super().__init__(label=label, xalign=0, **options)
            self._label = label

            # Set the size request of the label to its maximum possible size when inactive/active, this should stop the
            # sidebar from resizing its width when the largest child label becomes inactive/active.
            self.bold()
            max_width = self.get_layout().get_size().width / 1000
            self.unbold()
            max_width = max(max_width, self.get_layout().get_size().width / 1000)

            self.set_size_request(int(max_width + 1), -1)

        def bold(self) -> None:
            self.set_markup('<b>{}</b>'.format(GObject.markup_escape_text(self._label)))

        def unbold(self) -> None:
            self.set_markup(GObject.markup_escape_text(self._label))

    def _do_init(self, titles: Mapping[Any, str]) -> Gtk.Widget:
        self._titles = titles
        self._title_lbls = {}  # type: MutableMapping[Any, self._SidebarTitleLabel]

        self._widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, vexpand=True)
        self._widget.get_style_context().add_class('wizard-sidebar')
        self._widget.show_all()

        for title_id, title_text in titles.items():
            lbl = self._SidebarTitleLabel(label=title_text)
            lbl.show()
            self._widget.add(lbl)
            self._title_lbls[title_id] = lbl

        self.presenter.view_ready()

        return self._widget

    def set_active_title(self, title_id: Any) -> None:
        for title_lbl in self._title_lbls.values():
            title_lbl.unbold()

        self._title_lbls[title_id].bold()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@sidebar_cs.presenter(options=['active_title'])
class SidebarPresenter(Presenter['SidebarView']):
    def _do_init(self, active_title: Bindable[Any]) -> None:
        self._active_title = active_title
        self.__event_connections = [
            self._active_title.on_changed.connect(self._update_view_active_title)
        ]

        self._is_view_ready = False

    def view_ready(self) -> None:
        self._is_view_ready = True
        self._update_view_active_title()

    def _update_view_active_title(self) -> None:
        if self._is_view_ready is False: return

        self.view.set_active_title(self._active_title.get())

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
