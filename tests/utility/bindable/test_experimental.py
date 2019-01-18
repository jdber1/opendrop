import asyncio
import gc
import weakref
from unittest import mock

import pytest

from opendrop.utility.bindable.bindable import AtomicBindableVar
from opendrop.utility.bindable.experimental import if_expr


def _test_bindable_proxy(proxy, target):
    with mock.patch.multiple(target, _export=mock.DEFAULT, _raw_apply_tx=mock.DEFAULT):
        assert proxy._export() == target._export.return_value

        stub_tx = mock.Mock()
        assert proxy._raw_apply_tx(stub_tx) == target._raw_apply_tx.return_value
        target._raw_apply_tx.assert_called_once_with(stub_tx)


class TestIfExprJustInitialised:
    @pytest.fixture(autouse=True, params=[True, False])
    def fixture(self, request):
        cond_initial_value = request.param
        self.cond = AtomicBindableVar(cond_initial_value)
        self.true = mock.Mock()
        self.false = mock.Mock()
        self.result = if_expr(cond=self.cond, true=self.true, false=self.false)

    def get_target(self, cond):
        return self.true if cond else self.false

    def test_result_proxy(self):
        _test_bindable_proxy(proxy=self.result, target=self.get_target(self.cond.get()))

    def test_change_cond_changes_result_proxy_target(self):
        self.cond.set(not self.cond.get())
        _test_bindable_proxy(proxy=self.result, target=self.get_target(self.cond.get()))

    @pytest.mark.asyncio
    async def test_change_cond_changes_result_proxy_exports(self):
        next_target = self.get_target(not self.cond.get())

        new_tx = self.result.on_new_tx.wait()
        self.cond.set(not self.cond.get())
        new_tx = await asyncio.wait_for(new_tx, 0.1)

        assert new_tx == next_target._export.return_value


def test_if_expr_holds_strong_ref_to_arguments():
    cond, true, false = mock.Mock(), mock.Mock(), mock.Mock()
    cond_wr, true_wr, false_wr = (weakref.ref(x) for x in (cond, true, false))
    result = if_expr(cond, true, false)

    del cond, true, false
    gc.collect()

    assert all(x() is not None for x in (cond_wr, true_wr, false_wr))

    del result
    gc.collect()

    assert all(x() is None for x in (cond_wr, true_wr, false_wr))
