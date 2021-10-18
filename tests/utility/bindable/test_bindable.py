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


from unittest.mock import Mock, patch

import pytest

from opendrop.utility.bindable import abc, VariableBindable, AccessorBindable


class TestBindable:
    def setup(self) -> None:
        self.bindable = StubBindable()

    def test_get(self) -> None:
        with patch.object(self.bindable, '_get_value') as get_value:
            get_value.assert_not_called()

            value = self.bindable.get()

            assert value == get_value.return_value
            get_value.assert_called_once_with()

    def test_set(self) -> None:
        get_value = Mock(return_value=0)
        set_value = Mock()

        with patch.multiple(self.bindable, _get_value=get_value, _set_value=set_value):
            get_value.assert_not_called()

            self.bindable.set(123)

            set_value.assert_called_once_with(123)


class TestBindable_WithUnimplementedGetter:
    def setup(self) -> None:
        self.bindable = StubBindable()

        patcher = patch.object(self.bindable, '_get_value', Mock(side_effect=NotImplementedError))
        patcher.start()

    def test_set(self) -> None:
        with patch.object(self.bindable, '_set_value') as set_value:
            self.bindable.set(123)

            set_value.assert_called_once_with(123)


class TestBindable_OnChanged:
    def setup(self):
        self.bindable = StubBindable()

        self.changed_callback = Mock()
        self.bindable.on_changed.connect(self.changed_callback)

    def test_on_changed_fires_after_set(self):
        self.changed_callback.assert_not_called()

        self.bindable.set(123)

        self.changed_callback.assert_called_once_with()

    def test_on_changed_does_not_fire_if_set_to_same_value(self):
        value = object()

        with patch.object(self.bindable, '_get_value', Mock(return_value=value)):
            self.bindable.set(value)
            self.changed_callback.assert_not_called()


class TestBindable_OnChanged_With_CustomEqualityChecker:
    def setup(self):
        self.check_equals = Mock()

        self.bindable = StubBindable(check_equals=self.check_equals)

        self.changed_callback = Mock()
        self.bindable.on_changed.connect(self.changed_callback)

    def test_check_equals_is_passed_old_value_and_new_value(self):
        with patch.object(self.bindable, '_get_value', Mock(return_value=123)):
            self.bindable.set(456)
            self.check_equals.assert_called_with(123, 456)

    def test_on_changed_does_not_fire_if_check_equals_returns_true(self):
        self.check_equals.return_value = True

        self.bindable.set(123)

        self.changed_callback.assert_not_called()

    def test_on_changed_fires_if_check_equals_returns_false(self):
        self.check_equals.return_value = False

        self.changed_callback.assert_not_called()

        self.bindable.set(123)

        self.changed_callback.assert_called_once_with()


class TestVariableBindable:
    def setup(self):
        self.initial = object()
        self.bindable = VariableBindable(self.initial)

    def test_initial_value(self):
        assert self.bindable.get() == self.initial

    def test_set_and_get(self):
        new_value = object()

        self.bindable.set(new_value)

        assert self.bindable.get() == new_value


class TestAccessorBindable_WithGetterAndSetter:
    def setup(self):
        self.getter = Mock()
        self.setter = Mock()

        self.bindable = AccessorBindable(getter=self.getter, setter=self.setter)

    def test_get(self):
        self.getter.assert_not_called()

        value = self.bindable.get()
        assert value == self.getter.return_value

        self.getter.assert_called_once_with()

    def test_set(self):
        self.setter.assert_not_called()

        new_value = object()
        self.bindable.set(new_value)

        self.setter.assert_called_once_with(new_value)

    def test_poke(self):
        on_changed_callback = Mock()
        self.bindable.on_changed.connect(on_changed_callback)

        self.bindable.poke()

        on_changed_callback.assert_called_once_with()


class TestAccessorBindable_WithNoSetter:
    def setup(self):
        self.bindable = AccessorBindable(getter=Mock())

    def test_set(self):
        with pytest.raises(NotImplementedError):
            self.bindable.set(123)


class TestAccessorBindable_WithNoGetter:
    def setup(self):
        self.bindable = AccessorBindable(setter=Mock())

    def test_get(self):
        with pytest.raises(NotImplementedError):
            self.bindable.get()


class StubBindable(abc.Bindable):
    def _get_value(self):
        pass

    def _set_value(self, new_value):
        pass
