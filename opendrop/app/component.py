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
import pkg_resources
from gi.repository import Gtk, GdkPixbuf, Gio, GLib

from opendrop.mvp import ComponentSymbol, View, Presenter
from .conan import ConanSession, conan_root_cs
from .ift import IFTSession, ift_root_cs
from .main_menu import main_menu_cs
from .model import AppRootModel, AppMode

app_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@app_cs.view()
class AppRootView(View['AppRootPresenter', None]):
    APP_ICON = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/icon_256x256.png').read()
            )
        )
    )

    def _do_init(self) -> None:
        Gtk.Window.set_default_icon(self.APP_ICON)

        _, self._main_menu_window = self.new_component(
            main_menu_cs.factory(
                model=self.presenter.main_menu_model
            )
        )

        self._ift_window_cid = None
        self._conan_window_cid = None

        self.presenter.view_ready()

    def start_ift(self, session: IFTSession) -> None:
        assert self._ift_window_cid is None

        self._ift_window_cid, ift_window = self.new_component(
            ift_root_cs.factory(
                session=session
            )
        )

        self._main_menu_window.hide()
        ift_window.show()

    def _end_ift(self) -> None:
        assert self._ift_window_cid is not None
        self.remove_component(self._ift_window_cid)
        self._ift_window_cid = None

    def start_conan(self, session: ConanSession) -> None:
        assert self._conan_window_cid is None

        self._conan_window_cid, conan_window = self.new_component(
            conan_root_cs.factory(
                session=session
            )
        )

        self._main_menu_window.hide()
        conan_window.show()

    def _end_conan(self) -> None:
        assert self._conan_window_cid is not None
        self.remove_component(self._conan_window_cid)
        self._conan_window_cid = None

    def return_to_main_menu(self) -> None:
        if self._ift_window_cid is not None:
            self._end_ift()

        if self._conan_window_cid is not None:
            self._end_conan()

        self._main_menu_window.show()

    def hide_all_windows(self) -> None:
        self._main_menu_window.hide()
        self._ift_window.hide()


@app_cs.presenter(options=['model'])
class AppRootPresenter(Presenter['AppRootView']):
    def _do_init(self, model: AppRootModel) -> None:
        self._model = model

        self.main_menu_model = model.main_menu

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._model.bn_mode.on_changed.connect(
                self._hdl_model_mode_changed
            )
        ])

        self._hdl_model_mode_changed()

    def _hdl_model_mode_changed(self) -> None:
        mode = self._model.bn_mode.get()

        if mode is AppMode.MAIN_MENU:
            self.view.return_to_main_menu()
        elif mode is AppMode.IFT:
            new_ift_session = self._model.new_ift_session()
            self.view.start_ift(new_ift_session)
        elif mode is AppMode.CONAN:
            new_conan_session = self._model.new_conan_session()
            self.view.start_conan(new_conan_session)
        elif mode is AppMode.QUIT:
            self.component_destroy()

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
