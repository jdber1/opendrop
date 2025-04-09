# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


import math
import time

from gi.repository import GObject, GLib
from opendrop.appfw import Presenter, component, install


@component(
    template_path='./bar.ui',
)
class AnalysisFooterProgressBarPresenter(Presenter):
    _fraction = 0.0
    _text = ''

    _time_start = None
    _time_complete = None
    _count = True

    _elapsed_text = ''
    _center_text = ''
    _remaining_text = ''

    _mapped = False

    @install
    @GObject.Property(type=float)
    def fraction(self) -> float:
        return self._fraction

    @fraction.setter
    def fraction(self, fraction: float) -> None:
        self._fraction = fraction
        self.update_center_text()

    @install
    @GObject.Property(type=str)
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.update_center_text()

    @install
    @GObject.Property(type=bool, default=False)
    def count(self) -> bool:
        return self._count

    @count.setter
    def count(self, enabled: bool) -> None:
        self._count = enabled
        self.update_time_remaining()
        self.update_times_loop()

    @install
    @GObject.Property
    def time_start(self) -> float:
        return self._time_start

    @time_start.setter
    def time_start(self, time_start: float) -> None:
        self._time_start = time_start
        self.update_time_elapsed()

    @install
    @GObject.Property
    def time_complete(self) -> float:
        return self._time_complete

    @time_complete.setter
    def time_complete(self, time_complete: float) -> None:
        self._time_complete = time_complete
        self.update_time_remaining()

    def update_center_text(self) -> None:
        override_text = self._text
        if override_text:
            text = override_text
        else:
            text = '{:.0f}%'.format(self._fraction * 100)

        self._center_text = text
        self.notify('center-text')

    def update_time_elapsed(self) -> None:
        time_start = self._time_start
        text = ''
        if time_start is not None:
            time_elapsed = time.time() - time_start
            if time_elapsed >= 0:
                text = '{}'.format(pretty_time(time_elapsed))

        self._elapsed_text = text
        self.notify('elapsed-text')

    def update_time_remaining(self) -> None:
        time_complete = self._time_complete
        text = ''
        if time_complete is not None:
            time_remaining = time_complete - time.time()
            if time_remaining > 0:
                text = '-{}'.format(pretty_time(time_remaining))

        self._remaining_text = text
        self.notify('remaining-text')

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def center_text(self) -> str:
        return self._center_text

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def elapsed_text(self) -> str:
        return self._elapsed_text

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def remaining_text(self) -> str:
        return self._remaining_text

    def map(self, *_) -> None:
        self._mapped = True
        self.update_times_loop()

    def unmap(self, *_) -> None:
        self._mapped = False

    def update_times_loop(self) -> None:
        if hasattr(self, 'update_times_id'): return
        self.update_times_id = GLib.timeout_add_seconds(1, self.update_times_callback)

    def update_times_callback(self) -> bool:
        if not self._mapped or not self._count:
            del self.update_times_id
            return False

        self.update_time_elapsed()
        self.update_time_remaining()

        return True


# Helper function

def pretty_time(seconds: float) -> str:
    if not math.isfinite(seconds):
        return ''

    seconds = round(seconds)

    s = seconds % 60
    seconds //= 60
    m = seconds % 60
    seconds //= 60
    h = seconds

    return '{h:0>2}:{m:0>2}:{s:0>2}'.format(h=h, m=m, s=s)
