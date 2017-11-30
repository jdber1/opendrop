import asyncio

import pytest
from unittest.mock import call, Mock, patch
from pytest import raises

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View

from opendrop.mvp import handles


@pytest.fixture
def TestModel():
    class TestModel(Model):
        pass

    return TestModel

@pytest.fixture
def TestPresenter(TestModel, ITestView):
    class TestPresenter(Presenter[TestModel, ITestView]):
        def setup(self): pass

        def teardown(self): pass

        handle_event0 = handles('on_event0')(Mock())

        handle_event1 = handles('on_event1')(Mock())

    return TestPresenter


@pytest.fixture
def ITestView():
    class ITestView(IView):
        do0 = Mock()
        do1 = Mock()

    return ITestView


@pytest.fixture
def IOtherView():
    class IOtherView(IView):
        pass

    return IOtherView


@pytest.fixture
def TestView(ITestView):
    class TestView(View, ITestView):
        def setup(self): pass

        def teardown(self): pass

    return TestView


@pytest.fixture
def OtherView(IOtherView):
    class OtherView(View, IOtherView):
        def setup(self): pass

        def teardown(self): pass

    return OtherView


def test_presenter_simple_initialization(TestModel, TestView, TestPresenter):
    model = TestModel()
    view = TestView()

    test_presenter = TestPresenter(model, view)


def test_presenter_can_present_method(TestPresenter, TestView, OtherView):
    assert TestPresenter.can_present(TestView)
    assert not TestPresenter.can_present(OtherView)


def test_presenter_initialization_with_incompatible_view(TestModel, OtherView, TestPresenter):
    model = TestModel()
    view = OtherView()

    with raises(TypeError):
        presenter = TestPresenter(model, view)


@pytest.mark.asyncio
async def test_presenter_handle_events(TestModel, TestView, TestPresenter):
    model = TestModel()
    view = TestView()

    presenter = TestPresenter(model, view)

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


def test_presenter_call_view_methods(TestView, TestPresenter):
    model = None
    view = TestView()

    presenter = TestPresenter(model, view)

    presenter.view.do0()

    view.do0.assert_called_once_with()
    view.do1.assert_not_called()

    presenter.view.do1()

    view.do0.assert_called_once_with()
    view.do1.assert_called_once_with()


@pytest.mark.asyncio
async def test_view_methods_that_fire_events(TestView, OtherView):
    view = TestView()

    other_view1 = Mock()
    other_view2 = Mock()

    handle_close = Mock(spec=[])
    handle_spawn = Mock(spec=[])

    view.connect('on_close', handle_close)
    view.connect('on_spawn', handle_spawn)

    view.close()

    await asyncio.sleep(0)

    handle_close.assert_called_once_with(view, None)
    handle_spawn.assert_not_called()

    await asyncio.sleep(0)

    view.spawn(other_view1, modal=False)

    await asyncio.sleep(0)

    handle_spawn.assert_called_with(view, other_view1, False)
    view.spawn(other_view2, modal=True)

    await asyncio.sleep(0)

    handle_spawn.assert_has_calls([call(view, other_view1, False), call(view, other_view2, True)])


@pytest.mark.asyncio
async def test_view_fire_ignore_args(TestView):
    view = TestView()

    cb = Mock()

    view.connect('event0', cb)

    cb.assert_not_called()

    view.fire_ignore_args('event0', *('arg0', 'arg1'), **{'kwarg0': 'val0', 'kwarg1': 'val1'})

    await asyncio.sleep(0)

    cb.assert_called_once_with()


def test_presenter_lifecycle(TestModel, TestPresenter, TestView):
    # Test setup
    with patch.object(TestPresenter, 'setup', Mock()):
        presenter = TestPresenter(TestModel(), TestView())

        presenter.setup.assert_called_once_with()

    # Test teardown
    with patch.object(TestPresenter, 'teardown', Mock()):
        model = TestModel()
        view = TestView()
        presenter = TestPresenter(model, view)

        view.destroy()

        presenter.teardown.assert_called_once_with()


def test_view_lifecycle(TestView):
    # Test setup
    with patch.object(TestView, 'setup', Mock()):
        view = TestView()

        view.setup.assert_called_once_with()

    # Test teardown
    teardown_called = False

    def teardown(self):
        nonlocal teardown_called
        teardown_called = True

    with patch.object(TestView, 'teardown', teardown):
        view = TestView()
        view.destroy()

        assert teardown_called
