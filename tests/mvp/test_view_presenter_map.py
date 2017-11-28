from opendrop.mvp.ViewPresenterMap import ViewPresenterMap
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.IView import IView
from opendrop.mvp.View import View

TestModel = None


class IViewOne(IView):
    pass


class IViewTwo(IView):
    pass


class IViewThree(IView):
    pass


class PresenterOne(Presenter[TestModel, IViewOne]):
    pass


class PresenterTwo(Presenter[TestModel, IViewTwo]):
    pass


class PresenterThree(Presenter[TestModel, IViewThree]):
    pass


class ViewOne(View, IViewOne):
    pass


class ViewTwo(View, IViewTwo):
    pass


class ViewThree(View, IViewThree):
    pass


def test_view_presenter_map():
    views = [ViewOne, ViewTwo, ViewThree]
    presenters = [PresenterOne, PresenterTwo, PresenterThree]

    vpmap = ViewPresenterMap(views=views, presenters=presenters)

    assert vpmap.presenter_from_view(ViewOne) == PresenterOne

    assert vpmap.view_from_presenter(PresenterTwo) == ViewTwo