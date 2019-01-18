import gc
import weakref
from unittest import mock

import pytest

from opendrop.utility.bindable.set import SetBindableAddItemTx, SetBindableDiscardItemTx, BuiltinSetBindable, \
    ModifiableSetBindable


@pytest.mark.parametrize('x', (1, 2))
def test_add_item_tx(x):
    tx = SetBindableAddItemTx(x)
    mock_target = mock.MagicMock()
    mock_target.__contains__.return_value = False
    tx.silent_apply(mock_target)
    mock_target.add.assert_called_once_with(x, _bcast_tx=False)


@pytest.mark.parametrize('x', (1, 2))
def test_add_item_tx_target_already_contains(x):
    tx = SetBindableAddItemTx(x)
    mock_target = mock.MagicMock()
    mock_target.__contains__.return_value = True
    tx.silent_apply(mock_target)
    mock_target.add.assert_not_called()


@pytest.mark.parametrize('x', (1, 2))
def test_discard_item_tx(x):
    tx = SetBindableDiscardItemTx(x)
    mock_target = mock.MagicMock()
    mock_target.__contains__.return_value = True
    tx.silent_apply(mock_target)
    mock_target.discard.assert_called_once_with(x, _bcast_tx=False)


@pytest.mark.parametrize('x', (1, 2))
def test_discard_item_tx_target_does_not_contain(x):
    tx = SetBindableDiscardItemTx(x)
    mock_target = mock.MagicMock()
    mock_target.__contains__.return_value = False
    tx.silent_apply(mock_target)
    mock_target.discard.assert_not_called()


class StubSetBindable(ModifiableSetBindable):
    def _actual_add(self, x):
        pass

    def _actual_discard(self, x):
        pass

    def __contains__(self, x):
        pass

    def __len__(self):
        pass

    def __iter__(self):
        pass


@pytest.mark.parametrize('x', (1, 2))
@pytest.mark.asyncio
async def test_modifiable_set_bindable_add_item(x):
    set_bindable = StubSetBindable()
    with mock.patch.multiple(set_bindable, _actual_add=mock.DEFAULT, on_add=mock.DEFAULT):
        set_bindable.add(x)
        set_bindable._actual_add.assert_called_once_with(x)
        set_bindable.on_add.fire.assert_called_once_with(x)


@pytest.mark.parametrize('x', (1, 2))
@pytest.mark.asyncio
async def test_modifiable_set_bindable_discard_item(x):
    set_bindable = StubSetBindable()
    with mock.patch.multiple(set_bindable, _actual_discard=mock.DEFAULT, on_discard=mock.DEFAULT):
        set_bindable.discard(x)
        set_bindable._actual_discard.assert_called_once_with(x)
        set_bindable.on_discard.fire.assert_called_once_with(x)


class TestUnionDisjointSets:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.a = BuiltinSetBindable({1, 2, 3})
        self.b = BuiltinSetBindable({'a', 'b', 'c'})
        self.c = BuiltinSetBindable({'x', 'y', 'z'})
        self.union = self.a.union(self.b, self.c)

    def test_union_value(self):
        assert set(self.union) == set(self.a).union(self.b, self.c)

    def test_discard_from_a_source_set(self):
        with mock.patch.multiple(self.union, on_discard=mock.DEFAULT):
            self.a.discard(1)
            self.test_union_value()
            self.union.on_discard.fire.assert_called_once_with(1)

    def test_add_to_a_source_set(self):
        with mock.patch.multiple(self.union, on_add=mock.DEFAULT):
            self.b.add('d')
            self.test_union_value()
            self.union.on_add.fire.assert_called_once_with('d')

    def test_add_to_a_source_set_an_existing_item(self):
        with mock.patch.multiple(self.union, on_add=mock.DEFAULT):
            self.b.add(1)
            self.test_union_value()
            self.union.on_add.fire.assert_not_called()


class TestUnionIntersectingSets:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.a = BuiltinSetBindable({1, 2, 3})
        self.b = BuiltinSetBindable({2, 3, 4})
        self.c = BuiltinSetBindable({3, 4, 5})
        self.union = self.a.union(self.b, self.c)

    def test_union_value(self):
        assert set(self.union) == set(self.a).union(self.b, self.c)

    def test_discard_from_a_source_set(self):
        with mock.patch.multiple(self.union, on_discard=mock.DEFAULT):
            self.a.discard(2)
            self.test_union_value()
            self.union.on_discard.fire.assert_not_called()
            self.b.discard(2)
            self.union.on_discard.fire.assert_called_once_with(2)


def test_union_has_strong_ref_to_sources():
    a = BuiltinSetBindable({1, 2, 3})
    b = BuiltinSetBindable({'a', 'b', 'c'})
    c = BuiltinSetBindable({'x', 'y', 'z'})
    a_wr, b_wr, c_wr = (weakref.ref(x) for x in (a, b, c))

    union = a.union(b, c)

    del a, b, c
    gc.collect()

    assert all(x() is not None for x in (a_wr, b_wr, c_wr))

    del union
    gc.collect()

    assert all(x() is None for x in (a_wr, b_wr, c_wr))
