import asyncio
import gc
import weakref
from unittest.mock import Mock, call

import pytest
from pytest import raises

from opendrop.utility import events

SAMPLE_ARGS = (1, '2', [3], {4: 'four'}, object())
SAMPLE_KWARGS = dict(a=1, b='2', c=object())

SAMPLE_ONE_ARG = "Sample"


class TestEvent:
    def setup(self):
        self.event = events.Event()

    @pytest.mark.asyncio
    async def test_connect_and_fire(self):
        cb = Mock()

        conn = self.event.connect(cb)
        assert isinstance(conn, events.EventConnection)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)

        # Handler should be invoked by the event loop, so should not have been called before this coroutine yields.
        cb.assert_not_called()

        await asyncio.sleep(0)

        cb.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    @pytest.mark.asyncio
    async def test_connect_once(self):
        cb0, cb1 = Mock(), Mock()

        self.event.connect(cb0, once=False)
        self.event.connect(cb1, once=True)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0.1)

        cb0.assert_has_calls(2 * (call(*SAMPLE_ARGS, **SAMPLE_KWARGS),))
        cb1.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    def test_connect_once_scenario_2(self):
        # Test if a handler connected with `once=True` will be invoked more than once if the handler fires the event
        # it is connected to.
        cb_call_count = 0

        def cb():
            nonlocal cb_call_count

            cb_call_count += 1

            # Assert call count here as well so that the test won't get stuck in an infinite loop.
            assert cb_call_count == 1

            self.event.fire()

        self.event.connect(cb, once=True, immediate=True)
        self.event.fire()

        assert cb_call_count == 1

    @pytest.mark.asyncio
    async def test_connect_once_with_coroutine(self):
        cb = Mock()

        async def cb_(*args, **kwargs):
            await asyncio.sleep(0)
            cb(*args, **kwargs)

        self.event.connect(cb_, once=True)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0.1)

        cb.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        cbs = Mock(), Mock()

        for cb in cbs: self.event.connect(cb)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)

        assert all(not cb.called for cb in cbs)
        await asyncio.sleep(0)

        assert all(cb.call_args == call(*SAMPLE_ARGS, **SAMPLE_KWARGS) for cb in cbs)

    @pytest.mark.asyncio
    async def test_multiple_fires(self):
        cb = Mock()

        self.event.connect(cb)

        self.event.fire(*SAMPLE_ARGS)
        self.event.fire(**SAMPLE_KWARGS)
        await asyncio.sleep(0)

        cb.assert_has_calls((call(*SAMPLE_ARGS), call(**SAMPLE_KWARGS)))

    @pytest.mark.asyncio
    async def test_firing_order(self):
        order = []

        def       cb0(): order.append(0)
        def       cb1(): order.append(1)
        def       cb2(): order.append(2)
        async def cb3(): order.append(3)
        async def cb4(): order.append(4)
        def       cb5(): order.append(5)
        def       cb6(): order.append(6)

        self.event.connect(cb3)
        self.event.connect(cb0, immediate=True)
        self.event.connect(cb1, immediate=True)
        self.event.connect(cb2, immediate=True)
        self.event.connect(cb4)
        self.event.connect(cb5)
        self.event.connect(cb6)

        self.event.fire()
        await asyncio.sleep(0)

        assert order == sorted(order)

    @pytest.mark.asyncio
    async def test_event_connection_disconnect(self):
        cb0, cb1 = Mock(), Mock()

        conn0 = self.event.connect(cb0)
        conn1 = self.event.connect(cb1)

        conn0.disconnect()

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0)

        assert not cb0.called and cb1.call_args == call(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    def test_event_connection_disconnect_when_not_connected(self):
        conn = self.event.connect(Mock())
        conn.disconnect()

        with raises(events.NotConnected):
            conn.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_by_func(self):
        cb0, cb1 = Mock(), Mock()

        for cb in cb0, cb1: self.event.connect(cb)

        self.event.disconnect_by_func(cb0)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0)

        assert not cb0.called and cb1.call_args == call(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    @pytest.mark.asyncio
    async def test_event_disconnect_all(self):
        cb0, cb1, cb2 = Mock(), Mock(), Mock()

        for cb in cb0, cb1, cb2: self.event.connect(cb)
        self.event.disconnect_all()

        # Reconnect `cb2`.
        self.event.connect(cb2)

        self.event.fire(*SAMPLE_ARGS)
        await asyncio.sleep(0)

        assert all(not cb.called for cb in (cb0, cb1))
        cb2.assert_called_once_with(*SAMPLE_ARGS)

    def test_disconnect_by_func_when_not_connected(self):
        cb = Mock()

        self.event.connect(cb)
        self.event.disconnect_by_func(cb)

        # Try disconnecting a function that used to be connected.
        with raises(events.NotConnected):
            self.event.disconnect_by_func(cb)

        # Try disconnecting some random function that was never connected.
        with raises(events.NotConnected):
            self.event.disconnect_by_func(Mock())

    @pytest.mark.asyncio
    async def test_event_fire_ignore(self):
        cb0 = Mock()
        cb1 = Mock()

        conn0 = self.event.connect(cb0)
        conn1 = self.event.connect(cb1)

        self.event.fire_with_opts(SAMPLE_ARGS, block=(conn0,))

        await asyncio.sleep(0)

        cb0.assert_not_called()
        cb1.assert_called_once_with(*SAMPLE_ARGS)

    @pytest.mark.asyncio
    async def test_fire_immediate(self):
        cb = Mock()

        self.event.connect(cb, immediate=True)
        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        cb.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

        # Make sure the handler isn't called again for whatever reason.
        await asyncio.sleep(0.1)
        cb.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    @pytest.mark.asyncio
    async def test_fire_immediate_with_coroutine(self):
        async def cb(*args, **kwargs): pass

        with raises(ValueError):
            self.event.connect(cb, immediate=True)

    @pytest.mark.asyncio
    async def test_connect_and_fire_coroutine(self):
        cb = Mock()

        async def cb_(*args, **kwargs):
            cb(*args, **kwargs)

        self.event.connect(cb_)
        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0)

        cb.assert_called_once_with(*SAMPLE_ARGS, **SAMPLE_KWARGS)

    @pytest.mark.asyncio
    async def test_disconnect_with_force(self):
        checkpoint = 0

        async def cb():
            nonlocal checkpoint
            checkpoint = 1

            # Coroutine should exit here.
            await asyncio.sleep(0)

            checkpoint = 2

        conn = self.event.connect(cb)

        self.event.fire()
        await asyncio.sleep(0)
        conn.disconnect(_force=True)
        await asyncio.sleep(0)

        assert checkpoint == 1

    @pytest.mark.asyncio
    async def test_coroutine_disconnects_itself_with_force(self):
        checkpoint = 0

        async def cb():
            nonlocal checkpoint
            checkpoint = 1

            # Coroutine should exit here.
            conn.disconnect(_force=True)
            await asyncio.sleep(0)

            checkpoint = 2

        conn = self.event.connect(cb)

        self.event.fire()
        await asyncio.sleep(0.1)

        assert checkpoint == 1

    @pytest.mark.parametrize('fire_args, fire_kwargs, expected_result', [
        (tuple(), {}, None),
        (('abc',), {}, 'abc'),
        (('abc', 123), {}, ('abc', 123)),
        (('abc', 123), {'foo': 'bar'}, ('abc', 123))])
    @pytest.mark.asyncio
    async def test_wait_and_event_fire(self, fire_args, fire_kwargs, expected_result):
        fut = self.event.wait()
        self.event.fire(*fire_args, **fire_kwargs)
        assert await asyncio.wait_for(fut, timeout=0.1) == expected_result

    @pytest.mark.asyncio
    async def test_wait_and_event_disconnect_all(self):
        fut = self.event.wait()
        self.event.disconnect_all()
        assert fut.cancelled() is True

    def test_weak_ref(self):
        cb = Mock()
        cb_wref = weakref.ref(cb)

        self.event.connect(cb)

        del cb
        gc.collect()

        assert cb_wref() is None

    @pytest.mark.asyncio
    async def test_weak_ref_scenario_2(self):
        # Miscellaneous test scenario 2
        cb0, cb1 = Mock(), Mock()

        self.event.connect(cb0)
        self.event.connect(cb1)

        del cb0
        gc.collect()

        self.event.fire(*SAMPLE_ARGS)
        await asyncio.sleep(0)

        cb1.assert_called_once_with(*SAMPLE_ARGS)

    @pytest.mark.asyncio
    async def test_strong_ref(self):
        cb = Mock()
        cb_wref = weakref.ref(cb)

        self.event.connect(cb, strong_ref=True)

        del cb
        gc.collect()

        self.event.fire(*SAMPLE_ARGS)
        await asyncio.sleep(0)

        cb_wref().assert_called_with(*SAMPLE_ARGS)

    @pytest.mark.asyncio
    async def test_event_ignore_args_connect(self):
        cb = Mock()

        self.event.connect(cb, ignore_args=True)

        self.event.fire(*SAMPLE_ARGS, **SAMPLE_KWARGS)
        await asyncio.sleep(0)

        cb.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_weak_ref_with_method_type(self):
        cb = Mock()

        class ClassWithCallback:
            def cb_(self, *args, **kwargs):
                cb(*args, **kwargs)

        obj = ClassWithCallback()

        self.event.connect(obj.cb_)

        gc.collect()

        self.event.fire(*SAMPLE_ARGS)
        await asyncio.sleep(0)

        cb.assert_called_once_with(*SAMPLE_ARGS)

    @pytest.mark.asyncio
    async def test_is_func_connected(self):
        cb = Mock()

        assert not self.event.is_func_connected(cb)

        self.event.fire()
        await asyncio.sleep(0)

        cb.assert_not_called()

        self.event.connect(cb)
        assert self.event.is_func_connected(cb)

        self.event.fire(*SAMPLE_ARGS)
        await asyncio.sleep(0)

        assert self.event.is_func_connected(cb)

        cb.assert_called_once_with(*SAMPLE_ARGS)

    def test_is_func_connected_with_coroutine(self):
        async def cb(): pass

        assert not self.event.is_func_connected(cb)
        self.event.connect(cb)
        assert self.event.is_func_connected(cb)

    def test_is_func_connected_with_method_type(self):
        class ClassWithCallback:
            def cb(self): pass

        obj0 = ClassWithCallback()
        obj1 = ClassWithCallback()

        assert all(not self.event.is_func_connected(obj.cb) for obj in (obj0, obj1))
        self.event.connect(obj0.cb)
        assert self.event.is_func_connected(obj0.cb) and not self.event.is_func_connected(obj1.cb)

    def test_event_num_connections(self):
        cbs = [Mock() for i in range(5)]

        assert self.event.num_connections == 0

        # Track `num_connections` as handlers are connected.
        for i, cb in enumerate(cbs):
            self.event.connect(cb)
            assert self.event.num_connections == i + 1

        # Track `num_connections` as handlers are disconnected.
        for i, cb in enumerate(cbs):
            self.event.disconnect_by_func(cb)
            assert self.event.num_connections == len(cbs) - i - 1

        assert self.event.num_connections == 0


@pytest.mark.skip
def test_stub(): ...
