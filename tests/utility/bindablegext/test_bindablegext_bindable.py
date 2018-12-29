from unittest.mock import Mock

from gi.repository import GObject

from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop


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
    my_bn.on_changed.connect(cb, immediate=True)

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
    conn0 = my_bn.on_new_tx.connect(cb0, immediate=True)
    conn1 = my_bn.on_new_tx.connect(cb1, immediate=True)

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
    my_bn.on_changed.connect(cb, immediate=True)

    my_g_obj.set_property('my-prop', 0)

    cb.assert_called_once_with()
