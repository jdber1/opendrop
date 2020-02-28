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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable

log_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@log_cs.view()
class LogView(View['LogPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.ScrolledWindow()

        self._text_view = Gtk.TextView(
            monospace=True,
            editable=False,
            wrap_mode=Gtk.WrapMode.CHAR,
            hexpand=True,
            vexpand=True,
            margin=10
        )
        self._text_view.show()
        self._widget.add(self._text_view)

        self.presenter.view_ready()

        return self._widget

    def set_log_text(self, text: str) -> None:
        self._text_view.get_buffer().set_text(text)

    def _do_destroy(self) -> None:
        self._widget.destroy()


@log_cs.presenter(options=['in_log_text'])
class LogPresenter(Presenter['LogView']):
    def _do_init(self, in_log_text: Bindable[str]) -> None:
        self._bn_log_text = in_log_text
        self.__event_connections = []

    def view_ready(self):
        self.__event_connections.extend([
            self._bn_log_text.on_changed.connect(
                self._hdl_log_text_changed
            )
        ])

    def _hdl_log_text_changed(self) -> None:
        log_text = self._bn_log_text.get()
        self.view.set_log_text(log_text)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
