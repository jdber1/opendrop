import gc
import weakref

from opendrop.utility.bindable.bindable import Bindable, AbstractAtomicBindable
from opendrop.utility.bindable.binding import Binding, BindingMITM, AtomicBindingMITM


def test_binding_applies_new_tx_to_other_and_unbind():
    checkpoints = []

    class MyBindable(Bindable):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _export(self):
            pass

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('{.name}._apply_tx'.format(self), tx)
            )

        def alert(self, tx):
            self._bcast_tx(tx)

    bn0 = MyBindable(name='bn0')
    bn1 = MyBindable(name='bn1')

    binding = Binding(src=bn0, dst=bn1)

    # Clear `checkpoints` since `binding` would have called `_export()` on `bn0` and applied the returned transaction to
    # `bn1` which would have logged something to `checkpoints`.
    checkpoints = []

    bn0.alert(10)
    bn1.alert(15)

    assert checkpoints == [
        ('bn1._apply_tx', 10),
        ('bn0._apply_tx', 15)
    ]


def test_binding_initialise():
    checkpoints = []

    class MyBindable(Bindable):
        def __init__(self, name, initial_tx_to_export):
            super().__init__()
            self.name = name
            self.initial_tx_to_export = initial_tx_to_export

        def _export(self):
            checkpoints.append(
                ('{.name}._export'.format(self),)
            )
            return self.initial_tx_to_export

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('{.name}._apply_tx'.format(self), tx)
            )

    bn0_initial_tx_to_export = object()
    bn0 = MyBindable(name='bn0', initial_tx_to_export=bn0_initial_tx_to_export)
    bn1 = MyBindable(name='bn1', initial_tx_to_export=None)

    binding = Binding(src=bn0, dst=bn1)

    assert checkpoints == [
        ('bn0._export',),
        ('bn1._apply_tx', bn0_initial_tx_to_export),
    ]


def test_binding_unbind():
    checkpoints = []

    class MyBindable(Bindable):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _export(self):
            return None

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('{.name}._apply_tx'.format(self), tx)
            )

        def alert(self, tx):
            self._bcast_tx(tx)

    bn0 = MyBindable(name='bn0')
    bn1 = MyBindable(name='bn1')

    binding = Binding(src=bn0, dst=bn1)

    # Clear `checkpoints` since `binding` would have called `_export()` on `bn0` and applied the returned transaction to
    # `bn1` which would have logged something to `checkpoints`.
    checkpoints = []

    # Test binding is working as intended.
    bn0.alert(10)
    bn1.alert(15)

    assert checkpoints == [
        ('bn1._apply_tx', 10),
        ('bn0._apply_tx', 15)
    ]

    checkpoints = []

    # Unbind and then
    binding.unbind()

    # verify that transactions aren't being mirrored anymore as the two bindables are no longer bound.
    bn0.alert(object())
    bn1.alert(object())

    assert checkpoints == []

    # Test that `binding` no longer holds a reference to `bn0` and `bn1`
    bn0_wref = weakref.ref(bn0)
    bn1_wref = weakref.ref(bn1)

    del bn0, bn1
    gc.collect()

    assert bn0_wref() is None
    assert bn1_wref() is None


def test_chained_bindings():
    checkpoints = []

    class MyBindable(Bindable):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _export(self):
            pass

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('{.name}._apply_tx'.format(self), tx)
            )

        def alert(self, tx):
            self._bcast_tx(tx)

    bn0 = MyBindable(name='bn0')
    bn1 = MyBindable(name='bn1')
    bn2 = MyBindable(name='bn2')
    bn3 = MyBindable(name='bn3')

    binding01 = Binding(src=bn0, dst=bn1)
    binding12 = Binding(src=bn1, dst=bn2)
    binding32 = Binding(src=bn3, dst=bn2)

    # Diagram of bindings, arrow points from src to dst.
    #   bn0 -> bn1 -> bn2 <- bn3

    checkpoints = []

    # Test alert on bn0
    bn0.alert(0)

    assert checkpoints == [
        ('bn1._apply_tx', 0),
        ('bn2._apply_tx', 0),
        ('bn3._apply_tx', 0)
    ]

    checkpoints = []

    # Test alert on bn1
    bn1.alert(1)

    assert set(checkpoints) == {  # Ordering is not important
        ('bn0._apply_tx', 1),
        ('bn2._apply_tx', 1),
        ('bn3._apply_tx', 1)
    }

    checkpoints = []

    # Test alert on bn2
    bn2.alert(2)

    assert set(checkpoints) == {  # Ordering is not important
        ('bn0._apply_tx', 2),
        ('bn1._apply_tx', 2),
        ('bn3._apply_tx', 2)
    }

    checkpoints = []

    # Test alert on bn3
    bn3.alert(3)

    assert checkpoints == [
        ('bn2._apply_tx', 3),
        ('bn1._apply_tx', 3),
        ('bn0._apply_tx', 3)
    ]


def test_binding_with_mitm():
    checkpoints = []

    class MyBindable(Bindable[int]):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _export(self):
            checkpoints.append(
                ('{.name}._export'.format(self),)
            )
            return 3

        def _raw_apply_tx(self, tx):
            checkpoints.append(
                ('{.name}._apply_tx'.format(self), tx)
            )

        def alert(self, tx):
            self._bcast_tx(tx)

    class MyMITM(BindingMITM[int]):
        def to_dst(self, tx: int) -> int:
            checkpoints.append(('to_dst', tx))
            return tx + 1

        def to_src(self, tx: int) -> int:
            checkpoints.append(('to_src', tx))
            return tx * 2

    bn0 = MyBindable(name='bn0')
    bn1 = MyBindable(name='bn1')

    binding = Binding(src=bn0, dst=bn1, mitm=MyMITM())

    bn0.alert(10)
    bn1.alert(15)

    assert checkpoints == [
        # Initialisation of binding01
        ('bn0._export',),
        ('to_dst', 3),
        ('bn1._apply_tx', 4),

        # bn0.alert(10)
        ('to_dst', 10),
        ('bn1._apply_tx', 11),

        # bn1.alert(15)
        ('to_src', 15),
        ('bn0._apply_tx', 30)
    ]


def test_atomic_binding_mitm_inheriting():
    checkpoints = []

    class MyAtomicBindable(AbstractAtomicBindable):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _raw_get(self):
            checkpoints.append(
                ('{.name}._raw_get'.format(self),)
            )
            return 1

        def _raw_set(self, value):
            checkpoints.append(
                ('{.name}._raw_set'.format(self), value)
            )

    class MyMITM(AtomicBindingMITM[int]):
        def _atomic_to_dst(self, value: int) -> int:
            checkpoints.append(('_atomic_to_dst', value))
            return value + 1

        def _atomic_to_src(self, value: int) -> int:
            checkpoints.append(('_atomic_to_src', value))
            return value * 2

    bn0 = MyAtomicBindable(name='bn0')
    bn1 = MyAtomicBindable(name='bn1')
    bn2 = MyAtomicBindable(name='bn2')

    binding01 = Binding(src=bn0, dst=bn1, mitm=MyMITM())
    binding02 = Binding(src=bn0, dst=bn2)

    # Clear `checkpoints` since `binding` would have called `_export()` on `bn0` and applied the returned transaction to
    # `bn1` which would have logged something to `checkpoints`.
    checkpoints = []

    bn0.set(10)
    bn1.set(15)

    assert checkpoints == [
        # bn0.set(10)
        ('bn0._raw_set', 10),
        ('_atomic_to_dst', 10),
        ('bn1._raw_set', 11),
        ('bn2._raw_set', 10),

        # bn1.set(15)
        ('bn1._raw_set', 15),
        ('_atomic_to_src', 15),
        ('bn0._raw_set', 30),
        ('bn2._raw_set', 30),
    ]


def test_atomic_binding_mitm_functional_api():
    checkpoints = []

    class MyAtomicBindable(AbstractAtomicBindable):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _raw_get(self):
            checkpoints.append(
                ('{.name}._raw_get'.format(self),)
            )
            return 1

        def _raw_set(self, value):
            checkpoints.append(
                ('{.name}._raw_set'.format(self), value)
            )

    bn0 = MyAtomicBindable(name='bn0')
    bn1 = MyAtomicBindable(name='bn1')

    binding = Binding(src=bn0, dst=bn1, mitm=AtomicBindingMITM(
        to_dst=lambda v: v+1,
        to_src=lambda v: v*2
    ))

    # Clear `checkpoints` since `binding` would have called `_export()` on `bn0` and applied the returned transaction to
    # `bn1` which would have logged something to `checkpoints`.
    checkpoints = []

    bn0.set(10)
    bn1.set(15)

    assert checkpoints == [
        # bn0.set(10)
        ('bn0._raw_set', 10),
        ('bn1._raw_set', 11),

        # bn1.set(15)
        ('bn1._raw_set', 15),
        ('bn0._raw_set', 30),
    ]
