from unittest.mock import Mock

import pytest

from opendrop.utility.simplebindable.bindable import Bindable, BoxBindable, AccessorBindable


class TestBindable:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.my_bindable = StubBindable()
        self.my_bindable._get_value = Mock()
        self.my_bindable._set_value = Mock()

    def test_get(self):
        self.my_bindable._get_value.assert_not_called()

        value = self.my_bindable.get()

        assert value == self.my_bindable._get_value.return_value
        self.my_bindable._get_value.assert_called_once_with()

    def test_set(self):
        self.my_bindable._get_value.assert_not_called()

        new_value = object()
        self.my_bindable.set(new_value)

        self.my_bindable._set_value.assert_called_once_with(new_value)


class TestBindable_OnChanged:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.my_bindable = StubBindable()

        self.on_changed_callback = Mock()
        self.my_bindable.on_changed.connect(self.on_changed_callback)

    def test_on_changed_fires_after_set(self):
        self.on_changed_callback.assert_not_called()

        self.my_bindable.set(object())

        self.on_changed_callback.assert_called_once_with()

    def test_on_changed_does_not_fire_if_set_to_same_value(self):
        value = object()

        self.my_bindable._get_value = lambda: value
        self.my_bindable.set(value)

        self.on_changed_callback.assert_not_called()


class TestBindable_OnChanged_With_CustomEqualityChecker:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.check_equals = Mock()

        self.my_bindable = StubBindable(check_equals=self.check_equals)

        self.on_changed_callback = Mock()
        self.my_bindable.on_changed.connect(self.on_changed_callback)

    def test_check_equals_is_passed_current_value_and_new_value(self):
        current_value = object()
        self.my_bindable._get_value = lambda: current_value

        new_value = object()
        self.my_bindable.set(new_value)

        self.check_equals.assert_called_with(current_value, new_value)

    def test_on_changed_does_not_fire_if_check_equals_returns_true(self):
        self.check_equals.return_value = True

        self.my_bindable.set(object())

        self.on_changed_callback.assert_not_called()

    def test_on_changed_fires_if_check_equals_returns_false(self):
        self.check_equals.return_value = False

        self.on_changed_callback.assert_not_called()

        self.my_bindable.set(object())

        self.on_changed_callback.assert_called_once_with()


class TestBoxBindable:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.initial = object()
        self.my_bindable = BoxBindable(self.initial)

    def test_initial_value(self):
        assert self.my_bindable.get() == self.initial

    def test_set_and_get(self):
        new_value = object()
        self.my_bindable.set(new_value)

        assert self.my_bindable.get() == new_value


class TestAccessorBindable_WithGetterAndSetter:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.getter = Mock()
        self.setter = Mock()

        self.my_bindable = AccessorBindable(getter=self.getter, setter=self.setter)

    def test_get(self):
        self.getter.assert_not_called()

        value = self.my_bindable.get()
        assert value == self.getter.return_value

        self.getter.assert_called_once_with()

    def test_set(self):
        self.setter.assert_not_called()

        new_value = object()
        self.my_bindable.set(new_value)

        self.setter.assert_called_once_with(new_value)

    def test_poke(self):
        on_changed_callback = Mock()
        self.my_bindable.on_changed.connect(on_changed_callback)

        self.my_bindable.poke()

        on_changed_callback.assert_called_once_with()


class TestAccessorBindable_ReadOnly:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.getter = Mock()

        self.my_bindable = AccessorBindable(getter=Mock())

    def test_set(self):
        with pytest.raises(AttributeError):
            self.my_bindable.set(123)


class TestAccessorBindable_WriteOnly:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.my_bindable = AccessorBindable(setter=Mock())

    def test_get(self):
        with pytest.raises(AttributeError):
            self.my_bindable.get()


class StubBindable(Bindable):
    def _get_value(self):
        """stub"""

    def _set_value(self, new_value):
        """stub"""
