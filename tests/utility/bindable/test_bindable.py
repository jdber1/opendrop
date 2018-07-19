from unittest.mock import Mock

from pytest import raises

from opendrop.utility.bindable.bindable import Bindable, AtomicBindable, AtomicBindableVar, AtomicBindableAdapter


def test_bindable_send_tx():
    class MyBindable(Bindable):
        def _export(self):
            pass

        def _raw_apply_tx(self, tx):
            pass

    bn = MyBindable()

    cb = Mock()
    bn.on_new_tx.connect(cb, immediate=True)

    my_tx = object()
    bn._bcast_tx(my_tx)

    cb.assert_called_once_with(my_tx)


def test_bindable_apply_tx():
    checkpoints = []

    class MyBindableTx:
        def __init__(self, txs_to_return):
            self.txs_to_return = txs_to_return

    class MyBindable(Bindable[MyBindableTx]):
        def _export(self):
            pass

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('_raw_apply_tx', tx)
            )
            return tx.txs_to_return

    def hdl_new_tx(tx):
        checkpoints.append(
            ('hdl_new_tx', tx)
        )

    bn = MyBindable()
    hdl_new_tx_conn = bn.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Test _raw_apply_tx() returning None.
    tx = MyBindableTx(None)
    bn._apply_tx(tx)

    assert checkpoints == [
        ('_raw_apply_tx', tx),
        ('hdl_new_tx', tx)
    ]

    checkpoints = []

    # Test _raw_apply_tx() returning [1, 2, 3].
    tx = MyBindableTx([1, 2, 3])
    bn._apply_tx(tx)

    assert checkpoints == [
        ('_raw_apply_tx', tx),
        ('hdl_new_tx', 1),
        ('hdl_new_tx', 2),
        ('hdl_new_tx', 3)
    ]

    checkpoints = []

    # Test _raw_apply_tx() returning [] (empty list).
    tx = MyBindableTx([])
    bn._apply_tx(tx)

    assert checkpoints == [
        ('_raw_apply_tx', tx)
    ]

    checkpoints = []

    # Test _apply_tx() with block.
    def other_hdler(tx):
        checkpoints.append(
            ('other_hdler', tx)
        )

    bn.on_new_tx.connect(other_hdler, immediate=True)

    tx = MyBindableTx(None)
    bn._apply_tx(tx, block=(hdl_new_tx_conn,))

    assert checkpoints == [
        ('_raw_apply_tx', tx),
        ('other_hdler', tx)
    ]


# AtomicBindable tests.

def test_atomic_bn_get_and_set():
    checkpoints = []

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            checkpoints.append(('_raw_get',))
            return 4

        def _raw_set(self, v):
            checkpoints.append(('_raw_set', v))

    def hdl_new_tx(tx):
        checkpoints.append(('hdl_new_tx', tx))

    bn = MyAtomicBindable()
    bn.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Test get()
    assert bn.get() == 4
    assert checkpoints == [('_raw_get',)]

    checkpoints = []

    # Test set()
    bn.set(12)
    assert checkpoints == [
        ('_raw_set', 12),
        ('hdl_new_tx', MyAtomicBindable.create_tx(12))
    ]


def test_atomic_bn_apply_tx():
    checkpoints = []

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            pass

        def _raw_set(self, v):
            checkpoints.append(('_raw_set', v))

    def hdl_new_tx(tx):
        checkpoints.append(('hdl_new_tx', tx))

    tx = MyAtomicBindable.create_tx(23)

    bn = MyAtomicBindable()
    bn.on_new_tx.connect(hdl_new_tx, immediate=True)

    bn._apply_tx(tx)

    assert checkpoints == [
        ('_raw_set', 23),
        ('hdl_new_tx', tx)
    ]


def test_atomic_bn_export():
    checkpoints = []

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            checkpoints.append(('_raw_get',))
            return 9

        def _raw_set(self, v):
            pass

    def hdl_new_tx(tx):
        checkpoints.append(('hdl_new_tx', tx))

    bn = MyAtomicBindable()
    bn.on_new_tx.connect(hdl_new_tx, immediate=True)

    bn.poke()

    assert checkpoints == [
        ('_raw_get',),
        ('hdl_new_tx', MyAtomicBindable.create_tx(9))
    ]


def test_atomic_bn_poke():
    checkpoints = []

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            checkpoints.append(('_raw_get',))
            return 3

        def _raw_set(self, v):
            pass

    bn = MyAtomicBindable()

    assert bn._export() == MyAtomicBindable.create_tx(3)

    assert checkpoints == [
        ('_raw_get',)
    ]


def test_atomic_bn_property_adapter():
    checkpoints = []

    class MyClass:
        def __init__(self, bn):
            self.bn = bn

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            checkpoints.append(('_raw_get',))
            return 3

        def _raw_set(self, v):
            checkpoints.append(('_raw_set', v))

    prop_descriptor = AtomicBindable.property_adapter(lambda self: self.bn)

    obj = MyClass(bn=MyAtomicBindable())

    assert prop_descriptor.__get__(instance=obj, owner=type(obj)) == 3
    prop_descriptor.__set__(instance=obj, value=11)

    assert checkpoints == [
        ('_raw_get',),
        ('_raw_set', 11)
    ]


def test_atomic_bn_changed_event():
    checkpoints = []

    class MyAtomicBindable(AtomicBindable[int]):
        def _raw_get(self):
            pass

        def _raw_set(self, v):
            checkpoints.append(('_raw_set', v))

    def hdl_changed():
        checkpoints.append(('hdl_changed',))

    bn = MyAtomicBindable()
    bn.on_changed.connect(hdl_changed, immediate=True)

    bn.set(123)
    bn._apply_tx(MyAtomicBindable.create_tx(456))

    assert checkpoints == [
        ('_raw_set', 123),
        ('hdl_changed',),
        ('_raw_set', 456),
        ('hdl_changed',)
    ]


# AtomicBindableVar tests.

def test_atomic_bn_var_initialise():
    bn = AtomicBindableVar(0)
    assert isinstance(bn, AtomicBindable)


def test_atomic_bn_var_get():
    bn = AtomicBindableVar(4)
    assert bn.get() == 4


def test_atomic_bn_var_set():
    bn = AtomicBindableVar(0)
    bn.set(7)
    assert bn.get() == 7


# AtomicBindableAdapter tests.

def test_atomic_bn_adapter_initialise():
    bn = AtomicBindableAdapter()
    assert isinstance(bn, AtomicBindable)


def test_atomic_bn_adapter_get():
    bn = AtomicBindableAdapter()
    bn.getter = lambda: 4
    assert bn.get() == 4


def test_atomic_bn_adapter_get_without_getter():
    bn = AtomicBindableAdapter()

    with raises(ValueError):
        bn.get()


def test_atomic_bn_adapter_set():
    checkpoints = []

    bn = AtomicBindableAdapter()
    bn.setter = lambda v: checkpoints.append(('setter', v))

    bn.set(6)

    assert checkpoints == [
        ('setter', 6)
    ]


def test_atomic_bn_adapter_set_without_setter():
    bn = AtomicBindableAdapter()

    with raises(ValueError):
        bn.set(9)


def test_atomic_bn_initialise_with_getter_and_setter():
    getter = lambda: 1
    setter = lambda v: None

    bn = AtomicBindableAdapter(
        getter=getter,
        setter=setter
    )

    assert bn.getter == getter
    assert bn.setter == setter
