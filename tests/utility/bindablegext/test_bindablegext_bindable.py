import asyncio
from unittest import mock
from unittest.mock import Mock, patch

import pytest
from gi.repository import GObject

from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop, GObjectPropertyBindable


def test_link_atomic_bn_adapter_to_g_prop_getting_and_setting():
    checkpoints = []

    class MyGObject(GObject.Object):
        @GObject.Property
        def my_prop(self):
            checkpoints.append(('my_prop getter',))
            return 1

        @my_prop.setter
        def my_prop(self, value):
            checkpoints.append(('my_prop setter', value))

    my_bn = AtomicBindableAdapter()
    my_g_obj = MyGObject()

    link_atomic_bn_adapter_to_g_prop(my_bn, my_g_obj, 'my_prop')

    cb = Mock()
    my_bn.on_changed.connect(cb)

    assert my_bn.get() == 1

    cb.assert_not_called()
    my_bn.set(2)
    cb.assert_called_once_with()

    assert checkpoints == [
        ('my_prop getter',),
        ('my_prop setter', 2)
    ]


def test_link_atomic_bn_adapter_to_g_prop_apply_tx():
    class MyGObject(GObject.Object):
        @GObject.Property
        def my_prop(self):
            pass

        @my_prop.setter
        def my_prop(self, value):
            pass

    my_bn = AtomicBindableAdapter()
    my_g_obj = MyGObject()

    link_atomic_bn_adapter_to_g_prop(my_bn, my_g_obj, 'my_prop')

    cb0 = Mock()
    cb1 = Mock()
    conn0 = my_bn.on_new_tx.connect(cb0)
    conn1 = my_bn.on_new_tx.connect(cb1)

    tx = AtomicBindableAdapter._create_tx(0)
    my_bn._apply_tx(tx, block=(conn0,))

    cb0.assert_not_called()
    cb1.assert_called_once_with(tx)


def test_link_atomic_bn_adapter_to_g_prop_modify_g_prop():
    class MyGObject(GObject.Object):
        @GObject.Property
        def my_prop(self):
            pass

        @my_prop.setter
        def my_prop(self, value):
            pass

    my_bn = AtomicBindableAdapter()
    my_g_obj = MyGObject()

    link_atomic_bn_adapter_to_g_prop(my_bn, my_g_obj, 'my-prop')

    cb = Mock()
    my_bn.on_changed.connect(cb)

    my_g_obj.set_property('my-prop', 0)

    cb.assert_called_once_with()


def test_link_atomic_bn_adapter_to_g_prop_transform_to():
    class MyGObject(GObject.Object):
        my_prop_setter = Mock()
        my_prop = GObject.Property(setter=my_prop_setter)

    my_bn = AtomicBindableAdapter()
    my_g_obj = MyGObject()

    transform_to = Mock()
    link_atomic_bn_adapter_to_g_prop(my_bn, my_g_obj, 'my_prop', transform_to=transform_to)

    # Set the value of my_bn
    my_bn.set(2)

    transform_to.assert_called_once_with(2)
    MyGObject.my_prop_setter.assert_called_once_with(my_g_obj, transform_to.return_value)


def test_link_atomic_bn_adapter_to_g_prop_transform_from():
    class MyGObject(GObject.Object):
        my_prop_getter = Mock()
        my_prop = GObject.Property(getter=my_prop_getter)

    my_bn = AtomicBindableAdapter()
    my_g_obj = MyGObject()

    transform_from = Mock()
    link_atomic_bn_adapter_to_g_prop(my_bn, my_g_obj, 'my_prop', transform_from=transform_from)

    # Retrieve the value of my_bn
    assert my_bn.get() == transform_from.return_value
    transform_from.assert_called_once_with(MyGObject.my_prop_getter.return_value)


# Test GObjectPropertyBindable


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
