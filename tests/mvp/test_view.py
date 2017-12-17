import asyncio

import pytest

from unittest.mock import Mock, call, patch

from tests.mvp.samples import MyView


@pytest.mark.asyncio
async def test_view_methods_that_fire_events():
    view = MyView()

    handle_close = Mock(spec=[])

    view.connect('on_close', handle_close)

    view.close()

    await asyncio.sleep(0)

    handle_close.assert_called_once_with(view, None)


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
