import gc
import itertools
import weakref
from unittest.mock import Mock

import pytest

from opendrop.utility.events import Event
from opendrop.utility.bindable.apply import apply


class TestApply:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.my_function = Mock()
        self.bn_args = [MockBindable(), MockBindable()]
        self.bn_kwargs = {'abc': MockBindable(), 'def': MockBindable()}
        self.result = apply(self.my_function, *self.bn_args, **self.bn_kwargs)

    def test_result_changes_as_arguments_change(self):
        result_on_changed_callback = Mock()
        self.result.on_changed.connect(result_on_changed_callback)

        for bn_arg in itertools.chain(self.bn_args, self.bn_kwargs.values()):
            result_on_changed_callback.reset_mock()
            bn_arg.poke()
            result_on_changed_callback.assert_called_once_with()

    def test_result_value(self):
        self.my_function.assert_not_called()
        result_value = self.result.get()
        assert result_value == self.my_function.return_value

        args = [bn.get() for bn in self.bn_args]
        kwargs = {key: bn.get() for key, bn in self.bn_kwargs.items()}

        self.my_function.assert_called_once_with(*args, **kwargs)

    def test_result_set(self):
        # Can't set the value of result
        with pytest.raises(NotImplementedError):
            self.result.set(object())

    def test_no_indirect_references_to_result(self):
        result_wr = weakref.ref(self.result)
        del self.result
        gc.collect()

        assert result_wr() is None


class MockBindable:
    def __init__(self):
        self.on_changed = Event()
        self.get = Mock()
        self.set = Mock()

    def poke(self) -> None:
        self.on_changed.fire()

    def reset(self):
        self.get.reset_mock()
        self.set.reset_mock()
