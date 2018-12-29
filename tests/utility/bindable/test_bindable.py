from unittest.mock import Mock

import pytest
from pytest import raises

from opendrop.utility.bindable.bindable import Bindable, BaseAtomicBindable, AtomicBindableVar, AtomicBindableAdapter, \
    MutableSequenceBindable, MutableSequenceBindableSetItemTx, MutableSequenceBindableDelItemTx, \
    MutableSequenceBindableInsertTx, AtomicBindable


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


# BaseAtomicBindable tests.

def test_atomic_bn_get_and_set():
    checkpoints = []

    class MyAtomicBindable(BaseAtomicBindable[int]):
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

    class MyAtomicBindable(BaseAtomicBindable[int]):
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

    class MyAtomicBindable(BaseAtomicBindable[int]):
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

    class MyAtomicBindable(BaseAtomicBindable[int]):
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

    class MyAtomicBindable(BaseAtomicBindable[int]):
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

    class MyAtomicBindable(BaseAtomicBindable[int]):
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
    assert isinstance(bn, BaseAtomicBindable)


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
    assert isinstance(bn, BaseAtomicBindable)


def test_atomic_bn_adapter_get():
    bn = AtomicBindableAdapter()
    bn.getter = lambda: 4
    assert bn.get() == 4


def test_atomic_bn_adapter_get_without_getter():
    bn = AtomicBindableAdapter()

    with raises(AttributeError):
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

    with raises(AttributeError):
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


# Test MutableSequenceBindable
class MyMSB(MutableSequenceBindable):
    LOG_REAL_SETITEM = 'LOG_REAL_SETITEM'
    LOG_REAL_GETITEM = 'LOG_REAL_GETITEM'
    LOG_REAL_DELITEM = 'LOG_REAL_DELITEM'
    LOG_REAL_INSERT = 'LOG_REAL_INSERT'

    def __init__(self):
        super().__init__()

        # Used for testing.
        self.log = []

    def _real_setitem(self, i, v):
        self.log.append((self.LOG_REAL_SETITEM, i, v))

    def _real_getitem(self, i):
        self.log.append((self.LOG_REAL_GETITEM, i))

    def _real_delitem(self, i):
        self.log.append((self.LOG_REAL_DELITEM, i))

    def _real_insert(self, i, v):
        self.log.append((self.LOG_REAL_INSERT, i, v))

    def __len__(self) -> int:
        return 0


@pytest.mark.parametrize('tx, expect_i, expect_v', [
    (MutableSequenceBindableSetItemTx(0, 'my value'), 0, 'my value')
])
def test_mutable_sequence_bindable_setitem_tx_silent_apply(tx, expect_i, expect_v):
    msb = MyMSB()
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)
    hdl_setitem = Mock()
    msb.on_setitem.connect(hdl_setitem, immediate=True)

    # Apply the tx
    tx.silent_apply(msb)

    hdl_new_tx.assert_not_called()
    hdl_setitem.assert_called_once_with(expect_i, expect_v)
    assert msb.log == [(MyMSB.LOG_REAL_SETITEM, expect_i, expect_v)]


@pytest.mark.parametrize('tx, expect_i', [
    (MutableSequenceBindableDelItemTx(0), 0)
])
def test_mutable_sequence_bindable_delitem_tx_silent_apply(tx, expect_i):
    msb = MyMSB()
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)
    hdl_delitem = Mock()
    msb.on_delitem.connect(hdl_delitem, immediate=True)

    # Apply the tx
    tx.silent_apply(msb)

    hdl_new_tx.assert_not_called()
    hdl_delitem.assert_called_once_with(expect_i)
    assert msb.log == [(MyMSB.LOG_REAL_DELITEM, expect_i)]


@pytest.mark.parametrize('tx, expect_i, expect_v', [
    (MutableSequenceBindableInsertTx(0, 'my value'), 0, 'my value')
])
def test_mutable_sequence_bindable_insert_tx_silent_apply(tx, expect_i, expect_v):
    msb = MyMSB()
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)
    hdl_insert = Mock()
    msb.on_insert.connect(hdl_insert, immediate=True)

    # Apply the tx
    tx.silent_apply(msb)

    hdl_new_tx.assert_not_called()
    hdl_insert.assert_called_once_with(expect_i, expect_v)
    assert msb.log == [(MyMSB.LOG_REAL_INSERT, expect_i, expect_v)]


def test_mutable_sequence_bindable_setitem():
    msb = MyMSB()
    hdl_setitem = Mock()
    msb.on_setitem.connect(hdl_setitem, immediate=True)
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Call __setitem__
    msb.__setitem__(0, 'a string')

    hdl_setitem.assert_called_once_with(0, 'a string')
    assert msb.log == [(MyMSB.LOG_REAL_SETITEM, 0, 'a string')]
    assert hdl_new_tx.call_args is not None
    test_mutable_sequence_bindable_setitem_tx_silent_apply(hdl_new_tx.call_args[0][0], 0, 'a string')


def test_mutable_sequence_bindable_getitem():
    msb = MyMSB()
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Call __getitem__
    msb.__getitem__(0)

    hdl_new_tx.assert_not_called()
    assert msb.log == [(MyMSB.LOG_REAL_GETITEM, 0)]


def test_mutable_sequence_bindable_delitem():
    msb = MyMSB()
    hdl_delitem = Mock()
    msb.on_delitem.connect(hdl_delitem, immediate=True)
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Call __delitem__
    msb.__delitem__(0)

    hdl_delitem.assert_called_once_with(0)
    assert msb.log == [(MyMSB.LOG_REAL_DELITEM, 0)]
    assert hdl_new_tx.call_args is not None
    test_mutable_sequence_bindable_delitem_tx_silent_apply(hdl_new_tx.call_args[0][0], 0)


def test_mutable_sequence_bindable_insert():
    msb = MyMSB()
    hdl_insert = Mock()
    msb.on_insert.connect(hdl_insert, immediate=True)
    hdl_new_tx = Mock()
    msb.on_new_tx.connect(hdl_new_tx, immediate=True)

    # Call __delitem__
    msb.insert(0, 'a string')

    hdl_insert.assert_called_once_with(0, 'a string')
    assert msb.log == [(MyMSB.LOG_REAL_INSERT, 0, 'a string')]
    assert hdl_new_tx.call_args is not None
    test_mutable_sequence_bindable_insert_tx_silent_apply(hdl_new_tx.call_args[0][0], 0, 'a string')


def test_mutable_sequence_bindable_export():
    class MyMSBToTestExport(MyMSB):
        def __init__(self, lst) -> None:
            super().__init__()
            self._list = list(lst)

        def _real_getitem(self, i):
            super()._real_getitem(i)
            return self._list[i]

        def __len__(self):
            return len(self._list)

    l0 = MyMSBToTestExport([1, 2, 4, 8])
    l1 = MyMSB()

    # Export l0
    export_tx = l0._export()
    # Apply export_tx onto l1
    l1._apply_tx(export_tx)

    assert set(l1.log) == {(MyMSB.LOG_REAL_INSERT, i, v) for i, v in enumerate([1, 2, 4, 8])}
