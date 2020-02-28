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
from typing import Iterable, Callable, Any

from opendrop.utility.bindable import VariableBindable


class WizardModel:
    def __init__(self, pages: Iterable[Any]) -> None:
        self._pages = tuple(pages)

        self._interpage_actions = {}

        self.bn_current_page = VariableBindable(self._pages[0])

    def next_page(self) -> None:
        current_page = self.bn_current_page.get()
        next_page_idx = self._pages.index(current_page) + 1
        next_page = self._pages[next_page_idx]

        self.perform_interpage_action(current_page, next_page)

        self.bn_current_page.set(next_page)

    def prev_page(self) -> None:
        current_page = self.bn_current_page.get()
        prev_page_idx = self._pages.index(current_page) - 1
        prev_page = self._pages[prev_page_idx]

        self.perform_interpage_action(current_page, prev_page)

        self.bn_current_page.set(prev_page)

    def perform_interpage_action(self, start_page: Any, end_page: Any) -> None:
        if (start_page, end_page) not in self._interpage_actions:
            return

        callback = self._interpage_actions[(start_page, end_page)]

        callback()

    def register_interpage_action(self, start_page: Any, end_page: Any, callback: Callable[[], Any]) -> None:
        self._interpage_actions[(start_page, end_page)] = callback


class WizardPageControls:
    def __init__(self, do_next_page: Callable[[], Any], do_prev_page: Callable[[], Any]) -> None:
        self._do_next_page = do_next_page
        self._do_prev_page = do_prev_page

    def next_page(self) -> None:
        self._do_next_page()

    def prev_page(self) -> None:
        self._do_prev_page()
