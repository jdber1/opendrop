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
from enum import Enum
from typing import cast

from gi.repository import GLib, Gio, Gtk
from injector import inject

from opendrop.appfw import ComponentFactory
from opendrop.vendor import aioglib


class OpendropApplication(Gtk.Application):
    application_id = 'jdber1.opendrop'
    resource_base_path = None

    class _State(Enum):
        NONE = 0
        MAIN_MENU = 1
        IFT = 2
        CONAN = 3

    @inject
    def __init__(self, cf: ComponentFactory, **properties) -> None:
        super().__init__(**properties)

        self._loop = aioglib.GLibEventLoop(GLib.MainContext.default())
        self._cf = cf

        self._state = OpendropApplication._State.NONE
        self._current_window = None

    def do_startup(self) -> None:
        # Chain up to parent implementation.
        Gio.Application.do_startup.invoke(Gtk.Application, self)

        asyncio.set_event_loop(self._loop)
        self._loop.set_is_running(True)

    def do_activate(self) -> None:
        self._goto_main_menu()

    def do_shutdown(self) -> None:
        self._loop.set_is_running(False)

        # Chain up to parent implementation.
        Gio.Application.do_shutdown.invoke(Gtk.Application, self)

    def _goto_main_menu(self, *_) -> None:
        if self._state is OpendropApplication._State.MAIN_MENU:
            return

        self._clear_current_window()

        self._current_window = cast(Gtk.Window, self._cf.create('MainMenu'))
        self._current_window.show()

        self._current_window.connect('ift', self._goto_ift)
        self._current_window.connect('conan', self._goto_conan)

        self.add_window(self._current_window)

    def _goto_ift(self, *_) -> None:
        if self._state is OpendropApplication._State.IFT:
            return

        self._clear_current_window()

        self._current_window = cast(Gtk.Window, self._cf.create('IFTExperiment'))
        self._current_window.show()

        self._current_window.connect('destroy', self._goto_main_menu)

        self.add_window(self._current_window)

    def _goto_conan(self, *_) -> None:
        if self._state is OpendropApplication._State.CONAN:
            return

        self._clear_current_window()

        self._current_window = cast(Gtk.Window, self._cf.create('ConanExperiment'))
        self._current_window.show()

        self._current_window.connect('destroy', self._goto_main_menu)

        self.add_window(self._current_window)

    def _clear_current_window(self) -> None:
        if self._current_window is None: return
        self._current_window.destroy()
        self._current_window = None
