import asyncio
from unittest.mock import Mock

import pytest
from pytest import raises

from opendrop.mvp import handler_metadata
from tests.mvp.samples import MyModel, MyView, MyPresenter, OtherView


class CustomContextPresenter(MyPresenter):
    custom_context = Mock()
    new_context = Mock(return_value=custom_context)


def test_presenter_can_present_method():
    assert MyPresenter.can_control(MyView)
    assert not MyPresenter.can_control(OtherView)


def test_presenter_initialisation_with_incompatible_view():
    with raises(TypeError):
        MyPresenter(model=MyModel(), view=OtherView())


@pytest.mark.asyncio
async def test_presenter_handle_events():
    model = MyModel()
    view = MyView()

    presenter = MyPresenter(model=model, view=view)

    presenter.handle_event0.assert_not_called()
    presenter.handle_event1.assert_not_called()

    view.fire('on_event0')

    await asyncio.sleep(0)

    presenter.handle_event0.assert_called_once_with()
    presenter.handle_event1.assert_not_called()

    view.fire('on_event1', 'arg1', **{'kwarg1': 1, 'kwarg2': 'Text'})

    await asyncio.sleep(0)

    presenter.handle_event0.assert_called_once_with()
    presenter.handle_event1.assert_called_once_with('arg1', **{'kwarg1': 1, 'kwarg2': 'Text'})


def test_presenter_call_view_methods():
    model = MyModel()
    view = MyView()

    presenter = MyPresenter(model=model, view=view)

    presenter.view.do0()

    view.do0.assert_called_once_with()
    view.do1.assert_not_called()

    presenter.view.do1()

    view.do0.assert_called_once_with()
    view.do1.assert_called_once_with()


def test_presenter_get_handlers():
    presenter = MyPresenter(model=MyModel(), view=MyView())

    handlers = presenter.get_handlers()

    assert presenter.handle_event0 in handlers and presenter.handle_event1 in handlers

    for handler in presenter.get_handlers():
        assert handler_metadata.has_metadata(handler)


def test_presenter_handles_immediate():
    my_view = MyView()

    presenter = MyPresenter(model=MyModel(), view=my_view)

    my_view.fire('on_event2')

    presenter.handle_event2.assert_called_once_with()


@pytest.mark.asyncio
async def test_presenter_handles_source_name():
    my_model = MyModel()
    my_view = MyView()

    presenter = MyPresenter(model=my_model, view=my_view)

    my_view.fire('on_event3')

    await asyncio.sleep(0)

    presenter.handle_event3.assert_not_called()

    my_model.fire('on_event3')

    await asyncio.sleep(0)

    presenter.handle_event3.assert_called_once_with()

