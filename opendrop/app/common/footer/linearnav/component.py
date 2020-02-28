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


from typing import Optional, Callable, Any

from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter

linear_navigator_footer_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@linear_navigator_footer_cs.view(options=['back_label', 'next_label'])
class LinearNavigatorFooterView(View['LinearNavigatorFooterPresenter', Gtk.Widget]):
    def _do_init(self, back_label: str = '< Back', next_label: str = 'Next >') -> Gtk.Widget:
        self._widget = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            margin=10,
            hexpand=True,
        )

        self._back_btn = Gtk.Button(back_label)
        self._widget.pack_start(self._back_btn, expand=False, fill=False, padding=0)

        self._next_btn = Gtk.Button(next_label)
        self._widget.pack_end(self._next_btn, expand=False, fill=False, padding=0)

        self._back_btn.connect('clicked', lambda *_: self.presenter.back())
        self._next_btn.connect('clicked', lambda *_: self.presenter.next())

        self.presenter.view_ready()

        return self._widget

    def show_back_btn(self) -> None:
        self._back_btn.show()

    def hide_back_btn(self) -> None:
        self._back_btn.hide()

    def show_next_btn(self) -> None:
        self._next_btn.show()

    def hide_next_btn(self) -> None:
        self._next_btn.hide()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@linear_navigator_footer_cs.presenter(options=['do_back', 'do_next'])
class LinearNavigatorFooterPresenter(Presenter['LinearNavigatorFooterView']):
    def _do_init(
            self,
            do_back: Optional[Callable[[], Any]] = None,
            do_next: Optional[Callable[[], Any]] = None
    ) -> None:
        self._do_back = do_back
        self._do_next = do_next

    def view_ready(self) -> None:
        if self._do_back is not None:
            self.view.show_back_btn()
        else:
            self.view.hide_back_btn()

        if self._do_next is not None:
            self.view.show_next_btn()
        else:
            self.view.hide_next_btn()

    def back(self) -> None:
        self._do_back()

    def next(self) -> None:
        self._do_next()
