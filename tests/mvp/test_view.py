import asyncio
from unittest.mock import Mock

import pytest

from tests.mvp.samples import MyView, OtherView


@pytest.mark.asyncio
async def test_view_close():
    view = MyView()

    handle_close = Mock(spec=[])

    view.connect('on_close', handle_close)

    view.close(OtherView)

    await asyncio.sleep(0)

    handle_close.assert_called_once_with(view, OtherView)


@pytest.mark.asyncio
async def test_view_spawn():
    view = MyView()

    handle_spawn = Mock(spec=[])

    view.connect('on_spawn', handle_spawn)

    view.spawn(OtherView, child=False, args=(1, 2, 3), kwargs={'a': 1, 'b': 2, 'c': 3})

    await asyncio.sleep(0)

    handle_spawn.assert_called_once_with(view, OtherView, False, (1, 2, 3), {'a': 1, 'b': 2, 'c': 3})


@pytest.mark.asyncio
async def test_view_setup():
    view = MyView()

    handle_setup = Mock(spec=[])

    view.connect('on_setup_done', handle_setup)

    view.do_setup()

    await asyncio.sleep(0)

    handle_setup.assert_called_once_with()
