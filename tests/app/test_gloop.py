import asyncio

from unittest.mock import Mock

from timeit import time

import pytest


@pytest.mark.gloop
async def test_call_soon():
    cb = Mock(spec=[])

    cb.assert_not_called()

    asyncio.get_event_loop().call_soon(cb)

    await asyncio.sleep(0)

    cb.assert_called_once_with()


@pytest.mark.gloop
async def test_sleep():
    EPSILON = 0.001
    WAIT = 0.5

    start = time.time()

    await asyncio.sleep(WAIT)

    assert abs(time.time() - start - WAIT) < EPSILON