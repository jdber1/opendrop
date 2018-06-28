from unittest.mock import Mock

from opendrop.utility.events import Event

from opendrop.mvp.IView import IView
from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View


# Generic test classes

class MyModel(Model):
    pass


class IMyView(IView):
    do0 = Mock()
    do1 = Mock()


class MyView(View, IMyView):
    class _Events(View._Events):
        def __init__(self):
            super().__init__()

            self.on_event0 = Event()
            self.on_event1 = Event()
            self.on_event2 = Event()

    def setup(self): pass

    def teardown(self): pass


class MyPresenter(Presenter[MyModel, IMyView]):
    def setup(self): pass

    def teardown(self): pass


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