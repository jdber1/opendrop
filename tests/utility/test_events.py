import asyncio
import weakref

from unittest.mock import Mock, call

import functools

import gc
import pytest

from pytest import raises

import opendrop.utility.events as events


class EventSourceTestWrapper:
    def __init__(self):
        self._event_source = events.EventSource()

    def __getattr__(self, name):
        def f(*args, **kwargs):
            return getattr(self._event_source, name)('on_my_event', *args, **kwargs)

        return f

    @property
    def num_connected(self):
        return self._event_source.num_connected('on_my_event')


@pytest.fixture(params=['normal', 'event_source_wrapped'])
def event(request):
    """Create and return a new Event or a special wrapper object to test EventSource functionality"""
    if request.param == 'normal':
        return events.Event()
    elif request.param == 'event_source_wrapped':
        return EventSourceTestWrapper()


@pytest.fixture
def sample_str_args(request):
    """Create some sample arguments and return"""
    return tuple(["arg{}".format(i) for i in range(5)])


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
    cb0 = Mock()
    cb1 = Mock()

    event.connect(cb0, once=True)
    event.connect(cb1)

    cb0.assert_not_called()
    cb1.assert_not_called()

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb0.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)
    cb1.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)

    event.fire(*sample_str_args, **sample_str_str_kwargs)

    await asyncio.sleep(0)

    cb0.assert_called_once_with(*sample_str_args, **sample_str_str_kwargs)
    cb1.assert_has_calls([
        call(*sample_str_args, **sample_str_str_kwargs),
        call(*sample_str_args, **sample_str_str_kwargs)
    ])


def test_event_immediate_callback_connect_with_coroutine(event):
    async def async_cb(*args, **kwargs):
        pass

    with raises(ValueError):
        event.connect(async_cb, immediate=True)


@pytest.mark.asyncio
async def test_event_inline(event, sample_str_args):
    asyncio.get_event_loop().call_soon(functools.partial(event.fire, *sample_str_args))

    resp = await event.inline()

    assert resp == sample_str_args


@pytest.mark.asyncio
async def test_event_strong_ref(event, sample_str_args):
    cb = Mock()

    event.connect(cb, strong_ref=True)

    cb_weak_ref = weakref.ref(cb)

    del cb

    gc.collect()

    event.fire(*sample_str_args)

    await asyncio.sleep(0)

    assert cb_weak_ref() is not None

    cb_weak_ref().assert_called_with(*sample_str_args)


@pytest.mark.asyncio
async def test_event_weak_ref_with_method_type(event, sample_str_args):
    call_count = 0

    class A:
        def handler(self):
            nonlocal call_count

            call_count += 1

    a = A()

    event.connect(a.handler)

    event.fire()

    await asyncio.sleep(0)

    assert call_count == 1


def test_event_weak_ref(event):
    a = Mock()

    a_weak_ref = weakref.ref(a)

    event.connect(a)

    del a

    gc.collect()

    assert a_weak_ref() is None


@pytest.mark.asyncio
async def test_event_weak_ref2(event):
    a = Mock()
    b = Mock()

    a_weak_ref = weakref.ref(a)

    event.connect(a)
    event.connect(b)

    del a

    gc.collect()

    event.fire()

    await asyncio.sleep(0)

    b.assert_called_once_with()


def test_event_is_connected(event):
    cb = Mock()

    assert not event.is_connected(cb)
    event.connect(cb)

    assert event.is_connected(cb)


def test_event_num_connected(event):
    cb = Mock()

    assert event.num_connected == 0

    event.connect(cb)

    assert event.num_connected == 1