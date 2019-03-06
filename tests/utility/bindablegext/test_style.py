from unittest.mock import Mock

import pytest
from gi.repository import Gtk

from opendrop.utility.bindablegext.style import GStyleContextClassBindable


class TestGStyleContextClassBindable:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.style_context = Gtk.StyleContext()
        self.bindable = GStyleContextClassBindable(self.style_context, 'some-style-class')

    def test_initial_style_context_state(self):
        assert self.style_context.has_class('some-style-class') is False

    def test_initial_state(self):
        assert self.bindable.get() is False

    def test_set_truthy(self):
        self.bindable.set(ImplementsBool(is_truthy=True))

        assert self.style_context.has_class('some-style-class') is True
        assert self.bindable.get() is True

    def test_set_falsey(self):
        self.bindable.set(ImplementsBool(is_truthy=False))

        assert self.style_context.has_class('some-style-class') is False
        assert self.bindable.get() is False

    def test_style_context_changed(self):
        on_changed_callback = Mock()
        self.bindable.on_changed.connect(on_changed_callback)

        on_changed_callback.assert_not_called()

        self.style_context.emit('changed')

        on_changed_callback.assert_called_once_with()


class ImplementsBool:
    def __init__(self, is_truthy):
        self._is_truthy = is_truthy

    def __bool__(self) -> None:
        return self._is_truthy
