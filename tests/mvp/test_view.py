# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


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
