from unittest.mock import Mock

from opendrop.mvp.handler_metadata import is_handler, handles

from opendrop.mvp.Model import Model
from opendrop.mvp.View import View
from opendrop.mvp.Presenter import Presenter


def test_handles():
    class TestPresenter(Presenter):
        @handles("on_event0")
        def handle_event0(self):
            pass

        @handles("on_event1")
        def handle_event1(self):
            pass

    presenter = TestPresenter(Model(), View())

    handlers = presenter.get_handlers()

    assert presenter.handle_event0 in handlers and presenter.handle_event1 in handlers

    for handler in presenter.get_handlers():
        assert is_handler(handler)


def test_handles_immediate():
    class TestPresenter(Presenter):
        handle_event0 = handles('on_event0', immediate=True)(Mock())

    view = View()

    presenter = TestPresenter(Model(), view)

    view.fire('on_event0')

    presenter.handle_event0.assert_called_once_with()
