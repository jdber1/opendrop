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


import gc
import weakref
from unittest.mock import Mock

import pytest

from opendrop.utility.bindable.binding import Binding
from opendrop.utility.events import Event


class TestBinding:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.src_bindable = MockBindable()
        self.dst_bindable = MockBindable()

        self.binding = Binding(src=self.src_bindable, dst=self.dst_bindable)

    def test_dst_is_updated_with_src_value(self):
        self.dst_bindable.set.assert_called_once_with(
            self.src_bindable.get.return_value)

    def test_src_poke(self):
        self.src_bindable.reset()
        self.dst_bindable.reset()

        self.src_bindable.poke()

        self.dst_bindable.set.assert_called_once_with(
            self.src_bindable.get.return_value)

    def test_dst_poke(self):
        self.src_bindable.reset()
        self.dst_bindable.reset()

        self.dst_bindable.poke()

        self.src_bindable.set.assert_called_once_with(
            self.dst_bindable.get.return_value)

    def test_unbind_stops_propagating_changes(self):
        self.src_bindable.reset()
        self.dst_bindable.reset()

        self.binding.unbind()

        self.src_bindable.poke()
        self.dst_bindable.poke()

        self.src_bindable.get.assert_not_called()
        self.src_bindable.set.assert_not_called()
        self.dst_bindable.get.assert_not_called()
        self.dst_bindable.set.assert_not_called()

    def test_unbind_deletes_references_to_src_and_dst(self):
        src_bindable_wr = weakref.ref(self.src_bindable)
        dst_bindable_wr = weakref.ref(self.dst_bindable)

        del self.src_bindable
        del self.dst_bindable

        gc.collect()
        assert src_bindable_wr() is not None
        assert dst_bindable_wr() is not None

        self.binding.unbind()

        gc.collect()
        assert src_bindable_wr() is None
        assert dst_bindable_wr() is None


class TestBinding_With_ToDstTransform:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.src_bindable = MockBindable()
        self.dst_bindable = MockBindable()

        # Can't use a Mock object for to_dst() since it can sometimes have global referrers that prevent it from being
        # garbage collected (which is required for one of the test cases)
        def to_dst(x):
            self.to_dst_called_with.append(x)
            return self.to_dst_return_value

        self.to_dst_called_with = []
        self.to_dst_return_value = object()
        self.to_dst = to_dst

        self.binding = Binding(src=self.src_bindable, dst=self.dst_bindable, to_dst=self.to_dst)

    def test_dst_is_updated_with_src_value(self):
        self.dst_bindable.set.assert_called_once_with(
            self.to_dst_return_value)

        assert self.to_dst_called_with == [self.src_bindable.get.return_value]

    def test_src_poke(self):
        self.src_bindable.reset()
        self.dst_bindable.reset()
        self.to_dst_called_with.clear()

        self.src_bindable.poke()

        self.dst_bindable.set.assert_called_once_with(
            self.to_dst_return_value)

        assert self.to_dst_called_with == [self.src_bindable.get.return_value]

    def test_unbind_deletes_references_to_to_dst(self):
        to_dst_wr = weakref.ref(self.to_dst)

        del self.to_dst

        gc.collect()
        assert to_dst_wr() is not None

        self.binding.unbind()

        gc.collect()

        assert to_dst_wr() is None


class TestBinding_With_ToSrcTransform:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.src_bindable = MockBindable()
        self.dst_bindable = MockBindable()

        # Can't use a Mock object for to_dst() since it can sometimes have global referrers that prevent it from being
        # garbage collected (which is required for one of the test cases)
        def to_src(x):
            self.to_src_called_with.append(x)
            return self.to_src_return_value

        self.to_src_called_with = []
        self.to_src_return_value = object()
        self.to_src = to_src

        self.binding = Binding(src=self.src_bindable, dst=self.dst_bindable, to_src=self.to_src)

    def test_dst_poke(self):
        self.src_bindable.reset()
        self.dst_bindable.reset()
        self.to_src_called_with.clear()

        self.dst_bindable.poke()

        self.src_bindable.set.assert_called_once_with(
            self.to_src_return_value)

        assert self.to_src_called_with == [self.dst_bindable.get.return_value]

    def test_unbind_deletes_references_to_to_src(self):
        to_src_wr = weakref.ref(self.to_src)

        del self.to_src

        gc.collect()
        assert to_src_wr() is not None

        self.binding.unbind()

        gc.collect()

        assert to_src_wr() is None


class TestBinding_OneWay:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.src_bindable = MockBindable()
        self.dst_bindable = MockBindable()

        self.binding = Binding(src=self.src_bindable, dst=self.dst_bindable, one_way=True)

        self.src_bindable.reset()
        self.dst_bindable.reset()

    def test_src_poke(self):
        self.src_bindable.poke()

        self.dst_bindable.set.assert_called_once_with(
            self.src_bindable.get.return_value)

    def test_dst_poke(self):
        self.dst_bindable.poke()

        self.src_bindable.set.assert_not_called()


class MockBindable:
    def __init__(self):
        self.on_changed = Event()
        self.get = Mock()
        self.set = Mock()

    def poke(self) -> None:
        self.on_changed.fire()

    def reset(self):
        self.get.reset_mock()
        self.set.reset_mock()
