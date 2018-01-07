from unittest.mock import Mock

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View

from opendrop.mvp import handles


# Generic test classes

class MyModel(Model):
    pass


class IMyView(IView):
    do0 = Mock()
    do1 = Mock()


class MyView(View, IMyView):
    def setup(self): pass

    def teardown(self): pass


class MyPresenter(Presenter[MyModel, IMyView]):
    def setup(self): pass

    def teardown(self): pass

    handle_event0 = handles('view', 'on_event0')(Mock())

    handle_event1 = handles('view', 'on_event1')(Mock())

    handle_event2 = handles('view', 'on_event2', immediate=True)(Mock())

    handle_event3 = handles('model', 'on_event3')(Mock())


class IOtherView(IView):
    pass


class OtherView(View, IOtherView):
    def setup(self): pass

    def teardown(self): pass


# Classes for `test_view_presenter_map.py`

class IViewOne(IView):
    pass


class IViewTwo(IView):
    pass


class IViewThree(IView):
    pass


class PresenterOne(Presenter[MyModel, IViewOne]):
    pass


class PresenterTwo(Presenter[MyModel, IViewTwo]):
    pass


class PresenterThree(Presenter[MyModel, IViewThree]):
    pass


class ViewOne(View, IViewOne):
    pass


class ViewTwo(View, IViewTwo):
    pass


class ViewThree(View, IViewThree):
    pass