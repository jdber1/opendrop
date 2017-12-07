import asyncio

import pytest

from unittest.mock import Mock, call, patch

from tests.mvp.samples import MyView


@pytest.mark.asyncio
async def test_view_methods_that_fire_events():
    view = MyView()

    other_view1 = Mock()
    other_view2 = Mock()

    handle_close = Mock(spec=[])
    handle_spawn = Mock(spec=[])

    view.connect('on_close', handle_close)
    view.connect('on_spawn', handle_spawn)

    view.close()

    await asyncio.sleep(0)

    handle_close.assert_called_once_with(view, None)
    handle_spawn.assert_not_called()

    await asyncio.sleep(0)

    view.spawn(other_view1, modal=False)

    await asyncio.sleep(0)

    handle_spawn.assert_called_with(view, other_view1, False)
    view.spawn(other_view2, modal=True)

    await asyncio.sleep(0)

    handle_spawn.assert_has_calls([call(view, other_view1, False), call(view, other_view2, True)])


@pytest.mark.asyncio
async def test_view_events():
    view = MyView()

    cb0 = Mock()
    cb1 = Mock()
    cb2 = Mock()

    # Test `connect()`
    view.connect('event0', cb0)
    view.connect('event1', cb1)
    view.connect('event2', cb2)

    # Test `disconnect()`
    view.disconnect('event2', cb2)

    cb0.assert_not_called()
    cb1.assert_not_called()
    cb2.assert_not_called()

    # Test `fire()` and `fire_ignore_args()`
    view.fire_ignore_args('event0', *('arg0', 'arg1'), **{'kwarg0': 'val0', 'kwarg1': 'val1'})
    view.fire('event1', *('arg0', 'arg1'), **{'kwarg0': 'val0', 'kwarg1': 'val1'})
    view.fire('event2', *('arg0', 'arg1'), **{'kwarg0': 'val0', 'kwarg1': 'val1'})

    await asyncio.sleep(0)

    # Test handlers called correctly
    cb0.assert_called_once_with()
    cb1.assert_called_once_with(*('arg0', 'arg1'), **{'kwarg0': 'val0', 'kwarg1': 'val1'})
    cb2.assert_not_called()


def test_view_lifecycle():
    # Test setup
    with patch.object(MyView, 'setup', Mock()):
        view = MyView()

        view.setup.assert_called_once_with()

    # Test teardown
    teardown = Mock()

    with patch.object(MyView, 'teardown', teardown):
        view = MyView()
        view.destroy()

        # Avoid accessing attributes of `view` after `destroy()` has been called on it.
        teardown.assert_called_once_with()
