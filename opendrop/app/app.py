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


import asyncio
from gi.repository import Gtk, GLib, Gio
from enum import Enum

from opendrop.vendor import aioglib

from opendrop.appfw import Injector, Binder, Module, InstanceProvider
from .services.app import OpendropService
from .main_menu import MainMenu
from .ift import ift_root_cs, IFTSession
from .conan import conan_root_cs, ConanSession


class OpendropApplication(Gtk.Application):
    application_id = 'jdber1.opendrop'
    resource_base_path = None

    class _State(Enum):
        NONE = 0
        MAIN_MENU = 1
        IFT = 2
        CONAN = 3

    def __init__(self, **properties) -> None:
        super().__init__(**properties)
        self._loop = aioglib.GLibEventLoop(GLib.MainContext.default())

    def do_activate(self) -> None:
        self._root_injector = Injector(
            modules=[
                _InstallOpendropService(app=self),
            ],
            auto_bind=True,
        )

        self._state = OpendropApplication._State.NONE

        self._current_component = None
        self._current_window = None

        self._goto_main_menu()

    def _goto_main_menu(self) -> None:
        if self._state is OpendropApplication._State.MAIN_MENU:
            return

        self._clear_current_component()

        self._current_window = self._root_injector.create_object(MainMenu)
        self._current_window.show()

        self.add_window(self._current_window)

    def _goto_ift(self) -> None:
        if self._state is OpendropApplication._State.IFT:
            return

        self._clear_current_component()
        self._current_component = ift_root_cs.factory(
            session=self._new_ift_session()
        ).create()

        self.add_window(self._current_component.view_rep)
        self._current_component.view_rep.show()

    def _goto_conan(self) -> None:
        if self._state is OpendropApplication._State.CONAN:
            return

        self._clear_current_component()
        self._current_component = conan_root_cs.factory(
            session=self._new_conan_session()
        ).create()

        self.add_window(self._current_component.view_rep)
        self._current_component.view_rep.show()

    def _clear_current_component(self) -> None:
        if self._current_component is not None:
            self._current_component.destroy()

        if self._current_window is not None:
            self._current_window.destroy()

    def _new_ift_session(self) -> IFTSession:
        session = IFTSession(
            do_exit=self._goto_main_menu,
            loop=self._loop,
        )

        return session

    def _new_conan_session(self) -> ConanSession:
        session = ConanSession(
            do_exit=self._goto_main_menu,
            loop=self._loop,
        )

        return session

    def do_startup(self) -> None:
        # Chain up to parent implementation.
        Gio.Application.do_startup.invoke(Gtk.Application, self)

        asyncio.set_event_loop(self._loop)
        self._loop.set_is_running(True)

    def do_shutdown(self) -> None:
        self._loop.set_is_running(False)

        # Chain up to parent implementation.
        Gio.Application.do_shutdown.invoke(Gtk.Application, self)


class _InstallOpendropService(Module):
    def __init__(self, app: OpendropApplication) -> None:
        self._app = app

    def configure(self, binder: Binder) -> None:
        app = self._app
        app_service = OpendropService(
            do_main_menu=app._goto_main_menu,
            do_ift=app._goto_ift,
            do_conan=app._goto_conan,
            do_quit=app.quit,
        )

        binder.bind(OpendropService, to=InstanceProvider(app_service))
