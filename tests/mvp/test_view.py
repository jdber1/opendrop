import asyncio
from unittest.mock import Mock

import pytest

from tests.mvp.samples import MyView, OtherView


def test_view_close():
    view = MyView()

    view.close()


def test_view_spawn():
    view = MyView()

    view.spawn(OtherView, child=False, view_opts={'a': 1, 'b': 2, 'c': 3})


@pytest.mark.asyncio
async def test_view_setup():
    view = MyView()

    handle_setup = Mock(spec=[])

    view.connect('on_setup_done', handle_setup)

    view.do_setup()

    await asyncio.sleep(0)

    handle_setup.assert_called_once_with()
