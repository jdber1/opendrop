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


from unittest.mock import Mock

import pytest
from gi.repository import Gtk

from opendrop.utility.bindable.gextension import GStyleContextClassBindable


class TestGStyleContextClassBindable:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.style_context = Gtk.StyleContext()
        self.bindable = GStyleContextClassBindable(self.style_context, 'some-style-class')

    def test_initial_style_context_state(self):
        assert self.style_context.has_class('some-style-class') is False

    def test_initial_state(self):
        assert self.bindable.get() is False

    def test_set_truthy(self):
        self.bindable.set(ImplementsBool(is_truthy=True))

        assert self.style_context.has_class('some-style-class') is True
        assert self.bindable.get() is True

    def test_set_falsey(self):
        self.bindable.set(ImplementsBool(is_truthy=False))

        assert self.style_context.has_class('some-style-class') is False
        assert self.bindable.get() is False

    def test_style_context_changed(self):
        on_changed_callback = Mock()
        self.bindable.on_changed.connect(on_changed_callback)

        on_changed_callback.assert_not_called()

        self.style_context.emit('changed')

        on_changed_callback.assert_called_once_with()


class ImplementsBool:
    def __init__(self, is_truthy):
        self._is_truthy = is_truthy

    def __bool__(self) -> None:
        return self._is_truthy
