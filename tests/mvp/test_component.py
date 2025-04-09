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


from typing import Mapping, Any, Optional, cast as tcast
from unittest import mock
from unittest.mock import Mock, call

import pytest

from opendrop.mvp.component import ComponentSymbol, ComponentFactory, Component
from opendrop.utility.events import Event


def test_component_symbol_set_view():
    csymbol = ComponentSymbol()

    @csymbol.view(options=['a', 'b'])
    class MyView:
        pass

    assert csymbol._view_cls == MyView
    assert set(csymbol._view_options) == {'a', 'b'}


def test_component_symbol_set_view_with_no_options():
    csymbol = ComponentSymbol()

    @csymbol.view()
    class MyView:
        pass



def test_component_symbol_set_presenter():
    csymbol = ComponentSymbol()

    @csymbol.presenter(options=['x', 'y'])
    class MyPresenter:
        pass

    assert csymbol._presenter_cls == MyPresenter
    assert set(csymbol._presenter_options) == {'x', 'y'}


def test_component_symbol_set_presenter_with_no_options():
    csymbol = ComponentSymbol()

    @csymbol.presenter()
    class MyPresenter:
        pass



@mock.patch('opendrop.mvp.component.ComponentFactory')
def test_component_symbol_factory(MockComponentFactory):
    csymbol = MockComponentSymbol()
    cfactory = csymbol.factory(a=1, x=2)

    MockComponentFactory.assert_called_once_with(csymbol, options={'a': 1, 'x': 2})

    expected_cfactory = MockComponentFactory.return_value
    assert cfactory == expected_cfactory


@pytest.mark.parametrize(
    'options, expect_view, expect_presenter', [
        ({'a': 1, 'b': 2}, {'a': 1, 'b': 2}, {}),
        ({'x': 1, 'y': 2}, {}, {'x': 1, 'y': 2}),
        ({'a': 1, 'x': 2}, {'a': 1}, {'x': 2}),
        ({'a': 1}, {'a': 1}, {}),
        ({'x': 1}, {}, {'x': 1}),
    ]
)
def test_component_factory_create_constructs_view_and_presenter_with_right_arguments \
        (options, expect_view, expect_presenter):
    csymbol = MockComponentSymbol(view_options=['a', 'b'], presenter_options=['x', 'y'])

    cfactory = ComponentFactory(csymbol, options)

    cfactory.create()

    csymbol._view_cls.assert_called_once_with(env=None, options=expect_view)
    csymbol.presenter_cls.assert_called_once_with(env=None, options=expect_presenter)


def test_component_factory_create_with_environment():
    csymbol = MockComponentSymbol(view_options=['a', 'b'], presenter_options=['x', 'y'])

    cfactory = ComponentFactory(csymbol)

    mock_view_env = Mock()
    mock_presenter_env = Mock()

    cfactory.create(view_env=mock_view_env, presenter_env=mock_presenter_env)

    csymbol._view_cls.assert_called_once_with(env=mock_view_env, options={})
    csymbol.presenter_cls.assert_called_once_with(env=mock_presenter_env, options={})


@mock.patch('opendrop.mvp.component.Component')
def test_component_factory_create_constructs_component(MockComponent):
    csymbol = MockComponentSymbol(view_options=['a', 'b'], presenter_options=['x', 'y'])

    cfactory = ComponentFactory(csymbol)

    component = cfactory.create()

    new_view = csymbol._view_cls.return_value
    new_presenter = csymbol.presenter_cls.return_value

    MockComponent.assert_called_once_with(view=new_view, presenter=new_presenter)

    expect_component = MockComponent.return_value
    assert component == expect_component


def test_component_factory_create_too_many_options():
    csymbol = MockComponentSymbol(view_options=['a', 'b'], presenter_options=['x', 'y'])

    # Pass unknown options 'm' and 'n'
    cfactory = ComponentFactory(csymbol, options={'x': 1, 'y': 2, 'm': 100, 'n': 200})

    with pytest.raises(TypeError):
        cfactory.create()


def test_component_factory_fork():
    csymbol = MockComponentSymbol(view_options=['a', 'b'], presenter_options=['x', 'y'])

    cfactory1 = ComponentFactory(csymbol, options={'a': 1, 'x': 3})
    cfactory2 = cfactory1.fork(b=2, y=4)

    # Create using cfactory1
    cfactory1.create()

    csymbol.view_cls.assert_called_once_with(env=None, options={'a': 1})
    csymbol.presenter_cls.assert_called_once_with(env=None, options={'x': 3})

    # Reset mocks
    csymbol.view_cls.reset_mock()
    csymbol.presenter_cls.reset_mock()

    # Create using cfactory2
    cfactory2.create()

    csymbol.view_cls.assert_called_once_with(env=None, options={'a': 1, 'b': 2})
    csymbol.presenter_cls.assert_called_once_with(env=None, options={'x': 3, 'y': 4})


def test_component_inits_view_and_presenter():
    mock_view = Mock()
    mock_presenter = Mock()

    manager = Mock()
    manager.attach_mock(mock_view, 'mock_view')
    manager.attach_mock(mock_presenter, 'mock_presenter')

    component = Component(view=mock_view, presenter=mock_presenter)

    assert manager.mock_calls == [call.mock_presenter._init(mock_view), call.mock_view._init(mock_presenter)]


def test_component_view_rep():
    mock_view = Mock()
    component = Component(view=mock_view, presenter=Mock())

    assert component.view_rep == mock_view._init.return_value


def test_component_sets_presenter_component_hooks():
    mock_presenter = Mock()
    component = Component(view=Mock(), presenter=mock_presenter)

    assert mock_presenter._component_hooks.component_destroy == component.destroy


def test_component_sets_view_component_hooks():
    mock_view = Mock()
    component = Component(view=mock_view, presenter=Mock())

    assert mock_view._component_hooks.new_component == component._new_component_for_view
    assert mock_view._component_hooks.remove_component == component._remove_component_for_view


def test_component_new_component():
    mock_view = Mock()
    mock_presenter = Mock()
    component = Component(view=mock_view, presenter=mock_presenter)

    mock_cfactory = MockComponentFactory()
    new_child = component.new_component(mock_cfactory)

    mock_cfactory.create.assert_called_once_with(
        view_env=mock_view.extend_env.return_value,
        presenter_env=mock_presenter.extend_env.return_value
    )

    assert new_child == mock_cfactory.mock_child


def test_component_remove_component():
    component = Component(view=Mock(), presenter=Mock())

    mock_cfactory = MockComponentFactory()
    mock_child = tcast(Mock, component.new_component(mock_cfactory))

    component.remove_component(mock_child)

    mock_child.destroy.assert_called_once_with()

    # Should raise an error if we try to remove again.
    with pytest.raises(ValueError):
        component.remove_component(mock_child)


def test_component_removes_child_if_child_is_destroyed():
    component = Component(view=Mock(), presenter=Mock())

    mock_cfactory = MockComponentFactory()
    new_child = tcast(MockComponent, component.new_component(mock_cfactory))

    new_child.sim_destroy()

    # Should raise an error since child should have been automatically removed after it is destroyed.
    with pytest.raises(ValueError):
        component.remove_component(new_child)

    # Child should not be destroyed again by previous call to `component.remove_component()`
    new_child.destroy.assert_not_called()


def test_component_detaches_from_child_after_child_is_remove():
    component = Component(view=Mock(), presenter=Mock())

    mock_cfactory = MockComponentFactory()
    new_child = component.new_component(mock_cfactory)
    component.remove_component(new_child)

    assert new_child.on_destroyed.num_connections == 0


def test_component_destroy():
    mock_view = Mock()
    mock_presenter = Mock()

    component = Component(view=mock_view, presenter=mock_presenter)

    component.destroy()

    assert component.is_destroyed

    mock_view._destroy.assert_called_once_with()
    mock_presenter._destroy.assert_called_once_with()


def test_component_on_destroyed():
    component = Component(view=Mock(), presenter=Mock())

    callback = Mock()
    component.on_destroyed.connect(callback)

    component.destroy()

    callback.assert_called_once_with(component)


def test_component_destroy_destroys_child_components():
    component = Component(view=Mock(), presenter=Mock())

    mock_cfactories = [MockComponentFactory() for _ in range(3)]
    mock_children = [tcast(Mock, component.new_component(mock_cfactory)) for mock_cfactory in mock_cfactories]

    component.destroy()

    for mock_child in mock_children:
        mock_child.destroy.assert_called_once_with()


def test_component_new_component_for_view():
    mock_component = Mock()
    mock_child = mock_component.new_component.return_value
    mock_cfactory = Mock()

    return_value = Component._new_component_for_view(mock_component, mock_cfactory)

    mock_component.new_component.assert_called_once_with(mock_cfactory)

    expected_return_value = (
        mock_child,
        mock_child.view_rep,
    )

    assert return_value == expected_return_value


def test_component_remove_component_for_view():
    mock_component = Mock()
    mock_child = Mock()

    Component._remove_component_for_view(mock_component, mock_child)

    mock_component.remove_component.assert_called_once_with(mock_child)


class MockComponentSymbol(ComponentSymbol):
    def __init__(self, view_options: Optional[Mapping[str, Any]] = None,
                 presenter_options: Optional[Mapping[str, Any]] = None) -> None:
        super().__init__()

        self.view_cls = Mock()
        self.presenter_cls = Mock()

        self.view(options=view_options or {})(self.view_cls)
        self.presenter(options=presenter_options or {})(self.presenter_cls)


class MockComponentFactory:
    def __init__(self):
        self.mock_child = MockComponent()
        self.create = Mock(return_value=self.mock_child)


class MockComponent:
    def __init__(self):
        self.view_rep = None

        self.on_destroyed = Event()
        self.is_destroyed = False

        self.destroy = Mock(side_effect=self.sim_destroy)

    def sim_destroy(self):
        self.is_destroyed = True
        self.on_destroyed.fire(self)
