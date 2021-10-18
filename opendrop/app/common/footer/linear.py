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


from gi.repository import GObject

from opendrop.appfw import Presenter, component, install


@component(
    template_path='./linear.ui',
)
class LinearFooterPresenter(Presenter):
    _next_label = 'Next'
    _previous_label = 'Back'

    @install
    @GObject.Property(type=str)
    def next_label(self) -> str:
        return self._next_label

    @next_label.setter
    def next_label(self, text: str) -> None:
        self._next_label = text
        self.notify('next-visible')

    @install
    @GObject.Property(type=str)
    def previous_label(self) -> str:
        return self._previous_label
    
    @previous_label.setter
    def previous_label(self, text: str) -> None:
        self._previous_label = text
        self.notify('previous-visible')

    @install
    @GObject.Signal
    def next(self) -> None:
        pass

    @install
    @GObject.Signal
    def previous(self) -> None:
        pass
    
    @GObject.Property(type=bool, default=True, flags=GObject.ParamFlags.READABLE)
    def next_visible(self) -> bool:
        return self._next_label != ''

    @GObject.Property(type=bool, default=True, flags=GObject.ParamFlags.READABLE)
    def previous_visible(self) -> bool:
        return self._previous_label != ''
    
    def next_clicked(self, *_) -> None:
        self.emit('next')

    def previous_clicked(self, *_) -> None:
        self.emit('previous')
