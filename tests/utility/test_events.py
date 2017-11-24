import asyncio

from mock import Mock, call

import pytest

import opendrop.utility.events as events


@pytest.fixture
def event():
    """Create and return a new Event"""
    return events.Event()


@pytest.fixture(params=[0, 5])
def sample_str_args(request):
    """Create some sample arguments and return"""
    n = request.param

    return tuple(["arg{}".format(i) for i in range(n)])

@pytest.fixture(params=[0, 5])
def sample_str_str_kwargs(request):
    """Create some sample keyword arguments and return"""
    n = request.param

    return {"name{}".format(i): "val{}".format(i) for i in range(n)}


@pytest.mark.asyncio
async def test_event_fires_callback(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb)

    cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)


@pytest.mark.parametrize('num_callbacks', [10])
@pytest.mark.asyncio
async def test_event_fires_multiple_callbacks(event, sample_str_args, sample_str_str_kwargs, num_callbacks):
    cbs = [Mock() for i in range(num_callbacks)]

    for cb in cbs:
        event.connect(cb)
        cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    for cb in cbs:
        cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)


@pytest.mark.asyncio
async def test_event_disconnect(event):
    cb = Mock()

    event.connect(cb)
    event.fire()

    await asyncio.sleep(0)

    cb.assert_called_once()

    event.disconnect(cb)
    event.fire()

    await asyncio.sleep(0)

    cb.assert_called_once()


@pytest.mark.asyncio
async def test_event_disconnect_not_connected_listener(event):
    cb = Mock()

    with pytest.raises(events.ListenerNotConnected):
        event.disconnect(cb)


@pytest.mark.asyncio
async def test_event_multiple_connect(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb)
    event.connect(cb)
    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_has_calls([call(*sample_str_args, **sample_str_str_kwargs)]*2)


@pytest.mark.asyncio
async def test_event_multiple_fire(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb)
    event.fire(*sample_str_args)
    event.fire(**sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_has_calls([call(*sample_str_args), call(**sample_str_str_kwargs)])
