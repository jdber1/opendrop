from pytest import raises

from tests.mvp.samples import MyModel, MyView, MyPresenter, OtherView


def test_presenter_can_present_method():
    assert MyPresenter.can_control(MyView)
    assert not MyPresenter.can_control(OtherView)


def test_presenter_initialisation_with_incompatible_view():
    with raises(TypeError):
        MyPresenter(model=MyModel(), view=OtherView())


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
