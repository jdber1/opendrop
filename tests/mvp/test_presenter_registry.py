from opendrop.mvp.PresenterRegistry import PresenterRegistry

from tests.mvp.samples import ViewTwo, PresenterOne, PresenterTwo, PresenterThree


def test_presenter_registry():
    presenters = [PresenterOne, PresenterTwo, PresenterThree]

    pr = PresenterRegistry(presenters=presenters)

    assert pr.get_presenter_for_view(ViewTwo) == PresenterTwo
    assert pr.get_presenter_for_view(ViewTwo()) == PresenterTwo