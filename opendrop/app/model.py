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
import asyncio
from enum import Enum

from opendrop.utility.bindable import VariableBindable
from .conan import ConanSession
from .ift import IFTSession
from .main_menu import MainMenuModel


class AppRootModel:
    def __init__(self, *, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

        self.bn_mode = VariableBindable(AppMode.MAIN_MENU)

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
