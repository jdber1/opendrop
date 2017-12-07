import asyncio
from unittest.mock import Mock, patch

import pytest
from pytest import raises

from tests.mvp.samples import MyModel, MyView, MyPresenter, OtherView


def test_presenter_can_present_method():
    assert MyPresenter.can_present(MyView)
    assert not MyPresenter.can_present(OtherView)


def test_presenter_initialisation_with_incompatible_view():
    model = MyModel()
    view = OtherView()

    with raises(TypeError):
        MyPresenter(model, view)


@pytest.mark.asyncio
async def test_presenter_handle_events():
    model = MyModel()
    view = MyView()

    presenter = MyPresenter(model, view)

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
    model = None
    view = MyView()

    presenter = MyPresenter(model, view)

    presenter.view.do0()

    view.do0.assert_called_once_with()
    view.do1.assert_not_called()

    presenter.view.do1()

    view.do0.assert_called_once_with()
    view.do1.assert_called_once_with()


def test_presenter_lifecycle():
    # Test setup
    with patch.object(MyPresenter, 'setup', Mock()):
        presenter = MyPresenter(MyModel(), MyView())

        presenter.setup.assert_called_once_with()

    # Test teardown
    with patch.object(MyPresenter, 'teardown', Mock()):
        model = MyModel()
        view = MyView()
        presenter = MyPresenter(model, view)

        view.destroy()

        presenter.teardown.assert_called_once_with()
