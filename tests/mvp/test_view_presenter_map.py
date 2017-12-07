from opendrop.mvp.ViewPresenterMap import ViewPresenterMap

from tests.mvp.samples import ViewOne, ViewTwo, ViewThree, PresenterOne, PresenterTwo, PresenterThree


def test_view_presenter_map():
    views = [ViewOne, ViewTwo, ViewThree]
    presenters = [PresenterOne, PresenterTwo, PresenterThree]

    vpmap = ViewPresenterMap(views=views, presenters=presenters)

    assert vpmap.presenter_from_view(ViewOne) == PresenterOne

    assert vpmap.view_from_presenter(PresenterTwo) == ViewTwo