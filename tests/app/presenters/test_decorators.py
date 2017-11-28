from typing import Any
from unittest.mock import NonCallableMock

from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.handler_metadata import is_handler, handles


def test_handler_decorators():
    class TestPresenter(Presenter):
        @handles("on_event0")
        def handle_event0(self):
            pass

        @handles("on_event1")
        def handle_event1(self):
            pass

    model = NonCallableMock()
    view = NonCallableMock()

    presenter = TestPresenter(model, view)

    assert presenter.get_handlers() == {
        'on_event0': presenter.handle_event0,
        'on_event1': presenter.handle_event1,
    }

    for handler in presenter.get_handlers().values():
        assert is_handler(handler)
