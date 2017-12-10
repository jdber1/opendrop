import asyncio

from unittest.mock import Mock, call

import functools
import pytest

from pytest import raises

import opendrop.utility.events as events


class EventSourceTestWrapper:
    def __init__(self):
        self.event_source = events.EventSource()

    def connect(self, *args, **kwargs):
        return self.event_source.connect('on_my_event', *args, **kwargs)

    def disconnect(self, *args, **kwargs):
        return self.event_source.disconnect('on_my_event', *args, **kwargs)

    def fire(self, *args, **kwargs):
        return self.event_source.fire('on_my_event', *args, **kwargs)

    def fire_ignore_args(self, *args, **kwargs):
        return self.event_source.fire_ignore_args('on_my_event', *args, **kwargs)


@pytest.fixture(params=['normal', 'event_source_wrapped'])
def event(request):
    """Create and return a new Event or a special wrapper object to test EventSource functionality"""
    if request.param == 'normal':
        return events.Event()
    elif request.param == 'event_source_wrapped':
        return EventSourceTestWrapper()


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

    cb.assert_called_once_with()

    event.disconnect(cb)
    event.fire()

    await asyncio.sleep(0)

    cb.assert_called_once_with()


@pytest.mark.asyncio
async def test_event_disconnect_not_connected_listener(event):
    cb = Mock()

    with pytest.raises(events.HandlerNotConnected):
        event.disconnect(cb)


@pytest.mark.asyncio
async def test_event_multiple_connect(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb)
    event.connect(cb)
    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_has_calls([call(*sample_str_args, **sample_str_str_kwargs)] * 2)


@pytest.mark.asyncio
async def test_event_multiple_fire(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb)
    event.fire(*sample_str_args)
    event.fire(**sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_has_calls([call(*sample_str_args), call(**sample_str_str_kwargs)])


@pytest.mark.asyncio
async def test_event_fires_coroutine(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    async def async_cb(*args, **kwargs):
        nonlocal cb
        cb(*args, **kwargs)

    event.connect(async_cb)

    cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)


def test_event_immediate_callback_connect(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb, immediate=True)

    cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)


@pytest.mark.asyncio
async def test_event_ignore_args_connect(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb, ignore_args=True)

    cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with()


@pytest.mark.asyncio
async def test_event_fire_ignore_args(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb, ignore_args=True)

    cb.assert_not_called()

    event.fire_ignore_args(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with()


@pytest.mark.asyncio
async def test_event_once_connect(event, sample_str_args, sample_str_str_kwargs):
    cb = Mock()

    event.connect(cb, once=True)

    cb.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)


def test_event_immediate_callback_connect_with_coroutine(event):
    async def async_cb(*args, **kwargs):
        pass

    with raises(ValueError):
        event.connect(async_cb, immediate=True)
