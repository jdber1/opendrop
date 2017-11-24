import asyncio

from mock import Mock

from timeit import time

import pytest


@pytest.mark.gloop
async def test_call_soon():
    class Mock2:
        call_count = 0

        def __call__(self, *args, **kwargs):
            self.call_count += 1

        def assert_not_called(self):
            assert self.call_count == 0

        def assert_called_once(self):
            assert self.call_count == 1

    cb = Mock2()

    cb.assert_not_called()

    asyncio.get_event_loop().call_soon(cb)
    asyncio.get_event_loop().call_soon(print, "haadfsdfgsfgi")

    await asyncio.sleep(0)

    cb.assert_called_once()


@pytest.mark.gloop
async def test_sleep():
    EPSILON = 0.01
    WAIT = 0.5

    start = time.time()

    await asyncio.sleep(WAIT)

    assert abs(time.time() - start - WAIT) < EPSILON