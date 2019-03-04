import asyncio
from unittest.mock import Mock

import pytest
from gi.repository import GObject

from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable


class TestGObjectPropertyBindableSimple:
    @pytest.fixture(autouse=True)
    def fixture(self):
        class MyGObject(GObject.Object):
            my_prop_getter = Mock()
            my_prop_setter = Mock()
            my_prop = GObject.Property(my_prop_getter, my_prop_setter)

        self.MyGObject = MyGObject
        self.g_obj = self.MyGObject()
        self.g_obj_prop_bindable = GObjectPropertyBindable(self.g_obj, 'my-prop')

    def test_getting_and_setting(self):
        g_obj = self.g_obj
        prop_getter = g_obj.my_prop_getter
        prop_setter = g_obj.my_prop_setter
        g_obj_prop_bindable = self.g_obj_prop_bindable

        assert g_obj_prop_bindable.get() == prop_getter.return_value
        self.MyGObject.my_prop_getter.assert_called_once_with(g_obj)

        g_obj_prop_bindable.set(2)
        self.MyGObject.my_prop_setter.assert_called_once_with(g_obj, 2)

    def test_apply_tx(self):
        g_obj = self.g_obj
        prop_setter = g_obj.my_prop_setter
        g_obj_prop_bindable = self.g_obj_prop_bindable

        cb0 = Mock()
        cb1 = Mock()
        conn0 = g_obj_prop_bindable.on_new_tx.connect(cb0)
        conn1 = g_obj_prop_bindable.on_new_tx.connect(cb1)

        tx = AtomicBindableAdapter._create_tx(123)
        g_obj_prop_bindable._apply_tx(tx, block=(conn0,))

        cb0.assert_not_called()
        cb1.assert_called_once_with(tx)

        prop_setter.assert_called_once_with(g_obj, 123)

    @pytest.mark.asyncio
    async def test_modify_g_prop(self):
        g_obj = self.g_obj
        prop_getter = g_obj.my_prop_getter
        g_obj_prop_bindable = self.g_obj_prop_bindable

        on_changed_wait = g_obj_prop_bindable.on_changed.wait()
        on_new_tx_wait = g_obj_prop_bindable.on_new_tx.wait()

        g_obj.set_property('my-prop', 123)
        await asyncio.wait_for(on_changed_wait, 0.1)
        assert (await asyncio.wait_for(on_new_tx_wait, 0.1)).value == prop_getter.return_value


def test_g_object_property_bindable_transform_to():
    class MyGObject(GObject.Object):
        my_prop_setter = Mock()
        my_prop = GObject.Property(setter=my_prop_setter)

    g_obj = MyGObject()
    transform_to = Mock()
    g_obj_prop_bindable = GObjectPropertyBindable(g_obj, 'my_prop', transform_to=transform_to)

    # Set the value of my_bn
    g_obj_prop_bindable.set(123)

    transform_to.assert_called_once_with(123)
    MyGObject.my_prop_setter.assert_called_once_with(g_obj, transform_to.return_value)


def test_g_object_property_bindable_transform_from():
    class MyGObject(GObject.Object):
        my_prop_getter = Mock()
        my_prop = GObject.Property(getter=my_prop_getter)

    g_obj = MyGObject()
    transform_from = Mock()
    g_obj_prop_bindable = GObjectPropertyBindable(g_obj, 'my_prop', transform_from=transform_from)

    # Retrieve the value of my_bn
    value = g_obj_prop_bindable.get()

    assert value == transform_from.return_value
    transform_from.assert_called_once_with(MyGObject.my_prop_getter.return_value)
