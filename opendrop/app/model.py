import asyncio
from enum import Enum

from opendrop.utility.bindable import BoxBindable
from .conan import ConanSession
from .ift import IFTSession
from .main_menu import MainMenuModel


class AppRootModel:
    def __init__(self, *, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

        self.bn_mode = BoxBindable(AppMode.MAIN_MENU)

        self.main_menu = MainMenuModel(
            do_launch_ift=(
                lambda: self.bn_mode.set(AppMode.IFT)
            ),
            do_launch_conan=(
                lambda: self.bn_mode.set(AppMode.CONAN)
            ),
            do_exit=(
                lambda: self.bn_mode.set(AppMode.QUIT)
            ),
        )

    def new_ift_session(self) -> IFTSession:
        session = IFTSession(
            do_exit=(
                lambda: self.bn_mode.set(AppMode.MAIN_MENU)
            ),
            loop=self._loop,
        )

        return session

    def new_conan_session(self) -> ConanSession:
        session = ConanSession(
            do_exit=(
                lambda: self.bn_mode.set(AppMode.MAIN_MENU)
            ),
            loop=self._loop,
        )

        return session


class AppMode(Enum):
    QUIT = -1

    MAIN_MENU = 0
    IFT = 1
    CONAN = 2
