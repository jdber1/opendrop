from unittest.mock import Mock

from opendrop.mvp.view import View


def test_view_init_sets_presenter():
    class MyView(View):
        pass

    my_view = MyView()
    mock_presenter = Mock()
    my_view._init(presenter=mock_presenter)

    assert my_view.presenter == mock_presenter


def test_view_init_passes_options():
    class MyView(View):
        _do_init = Mock()

    my_view = MyView(options={'a': 1, 'b': 2})

    my_view._init(presenter=Mock())

    MyView._do_init.assert_called_with(a=1, b=2)


def test_view_init_return_value():
    class MyView(View):
        _do_init = Mock()

    my_view = MyView()

    return_value = my_view._init(presenter=Mock())

    assert return_value == my_view._do_init.return_value


def test_view_init_with_env():
    class MyView(View):
        pass

    my_env = {'a': 1, 'b': 2}
    my_view = MyView(env=my_env)
    my_view._init(presenter=Mock())

    assert my_env == dict(my_view.env)

    my_env['c'] = 3
    my_env['a'] = 100

    assert my_env == dict(my_view.env)


def test_view_init_with_no_env():
    class MyView(View):
        pass

    my_view = MyView()
    my_view._init(presenter=Mock())

    assert dict(my_view.env) == {}


def test_view_extend_env():
    class MyView(View):
        pass

    my_env = {'a': 1, 'b': 2}
    my_view = MyView(env=my_env)
    my_view._init(presenter=Mock())

    new_env = my_view.extend_env()

    assert dict(my_view.env) == dict(new_env)

    my_view.env['c'] = 3
    assert new_env['c'] == 3

    new_env['d'] = 4
    assert new_env['d'] == 4

    new_env['a'] = 100
    assert new_env['a'] == 100

    assert dict(my_view.env) == my_env


def test_view_destroy():
    class MyView(View):
        _do_destroy = Mock()

    my_view = MyView()
    my_view._init(presenter=Mock())

    my_view._destroy()

    my_view._do_destroy.assert_called_once_with()


def test_view_new_component():
    class MyView(View):
        pass

    my_view = MyView()
    mock_new_component = Mock()
    my_view._component_hooks.new_component = mock_new_component
    my_view._init(presenter=Mock())

    mock_cfactory = Mock()
    return_value = my_view.new_component(mock_cfactory)

    mock_new_component.assert_called_once_with(mock_cfactory)
    assert return_value == mock_new_component.return_value


def test_view_remove_component():
    class MyView(View):
        pass

    my_view = MyView()
    mock_remove_component = Mock()
    my_view._component_hooks.remove_component = mock_remove_component
    my_view._init(presenter=Mock())

    mock_component_id = Mock()
    return_value = my_view.remove_component(mock_component_id)

    mock_remove_component.assert_called_once_with(mock_component_id)
    assert return_value == mock_remove_component.return_value
