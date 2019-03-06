from unittest.mock import Mock

import pytest
from gi.repository import GObject

from opendrop.utility.bindablegext.property_bindable import GObjectPropertyBindable


class TestGObjectPropertyBindable:
    @pytest.fixture(autouse=True)
    def fixture(self):
        # Reset the property getter and setter mocks (since they are shared with all instances)
        MockGObjectWithProperty.prop_getter.reset_mock()
        MockGObjectWithProperty.prop_setter.reset_mock()

        self.g_obj = MockGObjectWithProperty()
        self.g_obj_prop_bindable = GObjectPropertyBindable(self.g_obj, 'prop')

    def test_get(self):
        g_obj = self.g_obj
        g_obj_prop_bindable = self.g_obj_prop_bindable

        value = g_obj_prop_bindable.get()

        assert value == MockGObjectWithProperty.prop_getter.return_value
        MockGObjectWithProperty.prop_getter.assert_called_once_with(g_obj)

    def test_set(self):
        g_obj = self.g_obj
        g_obj_prop_bindable = self.g_obj_prop_bindable

        new_value = object()
        g_obj_prop_bindable.set(new_value)

        MockGObjectWithProperty.prop_setter.assert_called_once_with(g_obj, new_value)

    def test_notify_g_obj_prop(self):
        g_obj = self.g_obj
        g_obj_prop_bindable = self.g_obj_prop_bindable

        on_changed_callback = Mock()
        g_obj_prop_bindable.on_changed.connect(on_changed_callback)

        on_changed_callback.assert_not_called()

        g_obj.notify('prop')

        on_changed_callback.assert_called_once_with()


class TestGObjectPropertyBindable_With_TransformTo:
    @pytest.fixture(autouse=True)
    def fixture(self):
        # Reset the property getter and setter mocks (since they are shared with all instances)
        MockGObjectWithProperty.prop_getter.reset_mock()
        MockGObjectWithProperty.prop_setter.reset_mock()

        self.g_obj = MockGObjectWithProperty()
        self.transform_to = Mock()
        self.g_obj_prop_bindable = GObjectPropertyBindable(self.g_obj, 'prop', transform_to=self.transform_to)

    def test_set(self):
        g_obj = self.g_obj
        transform_to = self.transform_to
        g_obj_prop_bindable = self.g_obj_prop_bindable

        new_value = object()
        g_obj_prop_bindable.set(new_value)

        transform_to.assert_called_with(new_value)
        MockGObjectWithProperty.prop_setter.assert_called_once_with(g_obj, transform_to.return_value)


class TestGObjectPropertyBindable_With_TransformFrom:
    @pytest.fixture(autouse=True)
    def fixture(self):
        # Reset the property getter and setter mocks (since they are shared with all instances)
        MockGObjectWithProperty.prop_getter.reset_mock()
        MockGObjectWithProperty.prop_setter.reset_mock()

        self.g_obj = MockGObjectWithProperty()
        self.transform_from = Mock()
        self.g_obj_prop_bindable = GObjectPropertyBindable(self.g_obj, 'prop', transform_from=self.transform_from)

    def test_get(self):
        transform_from = self.transform_from
        g_obj_prop_bindable = self.g_obj_prop_bindable

        value = g_obj_prop_bindable.get()

        transform_from.assert_called_with(MockGObjectWithProperty.prop_getter.return_value)
        assert value == transform_from.return_value


class MockGObjectWithProperty(GObject.Object):
    prop_getter = Mock()
    prop_setter = Mock()
    prop = GObject.Property(prop_getter, prop_setter)
