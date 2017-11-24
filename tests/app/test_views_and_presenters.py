from abc import ABCMeta

from mock import Mock
from pytest import raises

from opendrop.app.presenters.BasePresenter import BasePresenter
from opendrop.app.presenters.metadata import handles


def test_create_presenter_normal():
    class TestPresenter(BasePresenter[ITestView]):
        pass

    class ITestView(metaclass=ABCMeta):
        pass

    class TestView(ITestView):
        pass

    model = Mock()
    view = TestView()

    test_presenter = TestPresenter(model, view)


def test_create_presenter_incompatible_view():
    class TestPresenter(BasePresenter[ITestView]):
        pass

    class ITestView(metaclass=ABCMeta):
        pass

    class IOtherView(metaclass=ABCMeta):
        pass

    class TestView(IOtherView):
        pass

    model = Mock()
    view = TestView()

    with raises(TypeError):
        test_presenter = TestPresenter(model, view)

def test_presenter_handles_events():
    class TestPresenter(BasePresenter[ITestView]):
        @handles('on_event0')
        def handle_event0(self):
            pass

    class ITestView(metaclass=ABCMeta):
        pass

    class IOtherView(metaclass=ABCMeta):
        pass

    class TestView(BaseView, IOtherView):
        def do_event0(self):
            # make sure fire throws a type error or so if arguments don't match event handler
            self.fire('on_event0', 1, 2, 3)

    model = Mock()
    view = TestView()

    with raises(TypeError):
        test_presenter = TestPresenter(model, view)

def test_presenter_can_control_method():
    # blah blah blha

    # can control should work with classes and objects

    assert Presenter.can_control(View)
    assert not Presenter.can_control(OtherView)
    assert presenter.can_control(view)
    assert presenter.can_control(View)

    # and so on

# for changing views look at how javscript causes the document to change pages ?