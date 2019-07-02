from unittest.mock import Mock

from opendrop.mvp.presenter import Presenter


def test_presenter_init_sets_view():
    class MyPresenter(Presenter):
        pass

    my_presenter = MyPresenter()
    mock_view = Mock()
    my_presenter._init(view=mock_view)

    assert my_presenter.view == mock_view


def test_presenter_init_passes_options():
    class MyPresenter(Presenter):
        _do_init = Mock()

    my_presenter = MyPresenter(options={'a': 1, 'b': 2})

    my_presenter._init(view=Mock())

    MyPresenter._do_init.assert_called_with(a=1, b=2)


def test_presenter_init_with_env():
    class MyPresenter(Presenter):
        pass

    my_env = {'a': 1, 'b': 2}
    my_presenter = MyPresenter(env=my_env)
    my_presenter._init(view=Mock())

    assert my_env == dict(my_presenter.env)

    my_env['c'] = 3
    my_env['a'] = 100

    assert my_env == dict(my_presenter.env)


def test_presenter_init_with_no_env():
    class MyPresenter(Presenter):
        pass

    my_presenter = MyPresenter()
    my_presenter._init(view=Mock())

    assert dict(my_presenter.env) == {}


def test_presenter_extend_env():
    class MyPresenter(Presenter):
        pass

    my_env = {'a': 1, 'b': 2}
    my_presenter = MyPresenter(env=my_env)
    my_presenter._init(view=Mock())

    new_env = my_presenter.extend_env()

    assert dict(my_presenter.env) == dict(new_env)

    my_presenter.env['c'] = 3
    assert new_env['c'] == 3

    new_env['d'] = 4
    assert new_env['d'] == 4

    new_env['a'] = 100
    assert new_env['a'] == 100

    assert dict(my_presenter.env) == my_env


def test_presenter_destroy():
    class MyPresenter(Presenter):
        _do_destroy = Mock()

    my_presenter = MyPresenter()
    my_presenter._init(view=Mock())

    my_presenter._destroy()

    my_presenter._do_destroy.assert_called_once_with()


def test_presenter_component_destroy():
    class MyPresenter(Presenter):
        pass

    my_presenter = MyPresenter()
    mock_component_destroy = Mock()
    my_presenter._component_hooks.component_destroy = mock_component_destroy
    my_presenter._init(view=Mock())

    my_presenter.component_destroy()

    mock_component_destroy.assert_called_once_with()
