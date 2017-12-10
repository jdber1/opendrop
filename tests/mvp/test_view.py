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
