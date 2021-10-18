# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import asyncio
import gc
import weakref
from unittest.mock import Mock, call

import pytest
from pytest import raises

from opendrop.utility import events
from opendrop.utility.events import EventConnection


class TestEvent:
    def setup(self):
        self.event = events.Event()

    def test_connect_and_fire(self):
        cb = Mock()
        self.event.connect(cb)

        self.event.fire(1, 2, a='a', b='b')

        cb.assert_called_once_with(1, 2, a='a', b='b')

    def test_connect_once(self):
        cb0, cb1 = Mock(), Mock()

        self.event.connect(cb0, once=False)
        self.event.connect(cb1, once=True)

        self.event.fire(123)
        self.event.fire(123)

        cb0.assert_has_calls((call(123), call(123)))
        cb1.assert_called_once_with(123)

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

        self.event.connect(cb, once=True)
        self.event.fire()

        assert cb_call_count == 1

    def test_multiple_handlers(self):
        cbs = Mock(), Mock()
        for cb in cbs:
            self.event.connect(cb)

        self.event.fire(123)

        assert all(cb.call_args == call(123) for cb in cbs)

    def test_multiple_fires(self):
        cb = Mock()
        self.event.connect(cb)

        self.event.fire(123)
        self.event.fire(abc='abc')

        cb.assert_has_calls((call(123), call(abc='abc')))

    def test_firing_order(self):
        order = []

        def cb0(): order.append(1)
        def cb1(): order.append(2)
        def cb2(): order.append(3)
        def cb3(): order.append(0)

        self.event.connect(cb3)
        self.event.connect(cb0)
        self.event.connect(cb1)
        self.event.connect(cb2)

        self.event.fire()

        assert order == sorted(order)

    def test_EventConnection_disconnect(self):
        cb0, cb1 = Mock(), Mock()
        conn0 = self.event.connect(cb0)
        conn1 = self.event.connect(cb1)

        conn0.disconnect()
        assert conn0.status is EventConnection.Status.DISCONNECTED

        self.event.fire(123)
        assert not cb0.called and cb1.mock_calls == [call(123)]

    def test_disconnect_by_func(self):
        cb0, cb1 = Mock(), Mock()
        conn0 = self.event.connect(cb0)
        conn1 = self.event.connect(cb1)

        self.event.disconnect_by_func(cb0)
        assert conn0.status is EventConnection.Status.DISCONNECTED

        self.event.fire(123)
        assert not cb0.called and cb1.mock_calls == [call(123)]

    def test_EventConnection_disconnect_when_not_connected(self):
        conn = self.event.connect(Mock())
        conn.disconnect()

        with raises(events.NotConnected):
            conn.disconnect()

    def test_disconnect_all(self):
        cb0, cb1, cb2 = Mock(), Mock(), Mock()
        for cb in cb0, cb1, cb2:
            self.event.connect(cb)

        self.event.disconnect_all()

        # Reconnect `cb2`.
        self.event.connect(cb2)

        self.event.fire(123)

        assert all(not cb.called for cb in (cb0, cb1))
        cb2.assert_called_once_with(123)

    def test_disconnect_by_func_when_not_connected(self):
        cb = Mock()
        self.event.connect(cb).disconnect()

        # Try disconnecting a function that used to be connected.
        with raises(events.NotConnected):
            self.event.disconnect_by_func(cb)

        # Try disconnecting some random function that was never connected.
        with raises(events.NotConnected):
            self.event.disconnect_by_func(Mock())

    def test_fire_block_some_connections(self):
        cb0 = Mock()
        cb1 = Mock()
        conn0 = self.event.connect(cb0)
        conn1 = self.event.connect(cb1)

        self.event.fire_with_opts(args=[123], block=(conn0,))

        cb0.assert_not_called()
        cb1.assert_called_once_with(123)

    @pytest.mark.parametrize(
        'fire_args, fire_kwargs, expected_result', [
            (tuple(), {}, None),
            (('abc',), {}, 'abc'),
            (('abc', 123), {}, ('abc', 123)),
            (('abc', 123), {'foo': 'bar'}, ('abc', 123))
        ]
    )
    @pytest.mark.asyncio
    async def test_wait(self, fire_args, fire_kwargs, expected_result):
        coro = self.event.wait()
        self.event.fire(*fire_args, **fire_kwargs)
        assert await asyncio.wait_for(coro, timeout=0.1) == expected_result

    @pytest.mark.asyncio
    async def test_wait_and_disconnect_all(self):
        coro = self.event.wait()
        self.event.disconnect_all()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(coro, timeout=0.1)

    @pytest.mark.asyncio
    async def test_wait_and_cancel_wait_task(self, event_loop):
        coro = self.event.wait()
        wait_task = event_loop.create_task(coro)

        # Hand over control to event loop for a bit to begin wait_task
        await asyncio.sleep(0.1)

        wait_task.cancel()

        # This should not raise any errors about attempting to set the result of a cancelled future.
        self.event.fire(123)

    def test_weak_ref_by_default(self):
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
        self.event.connect(cb0, weak_ref=False)
        self.event.connect(cb1, weak_ref=False)

        del cb0
        gc.collect()

        self.event.fire(123)
        await asyncio.sleep(0)

        cb1.assert_called_once_with(123)

    def test_connect_with_weak_ref_false(self):
        cb = Mock()
        cb_wref = weakref.ref(cb)

        self.event.connect(cb, weak_ref=False)

        del cb
        gc.collect()

        self.event.fire(123)
        cb_wref().assert_called_with(123)

    def test_connect_with_ignore_args_true(self):
        cb = Mock()
        self.event.connect(cb, ignore_args=True)

        self.event.fire(123, abc='abc')

        cb.assert_called_once_with()

    def test_weak_ref_with_method_type(self):
        cb = Mock()

        class ClassWithCallback:
            def cb(self, *args, **kwargs):
                cb(*args, **kwargs)

        obj = ClassWithCallback()
        self.event.connect(obj.cb, weak_ref=True)

        gc.collect()

        self.event.fire(123)
        cb.assert_called_once_with(123)

    def test_is_func_connected(self):
        cb = Mock()

        assert not self.event.is_func_connected(cb)

        self.event.fire()
        cb.assert_not_called()

        self.event.connect(cb)
        assert self.event.is_func_connected(cb)

        self.event.fire(123)
        assert self.event.is_func_connected(cb)
        cb.assert_called_once_with(123)

    def test_is_func_connected_with_method_type(self):
        class ClassWithCallback:
            def cb(self): pass

        obj0 = ClassWithCallback()
        obj1 = ClassWithCallback()

        assert all(not self.event.is_func_connected(obj.cb) for obj in (obj0, obj1))
        self.event.connect(obj0.cb)
        assert self.event.is_func_connected(obj0.cb) and not self.event.is_func_connected(obj1.cb)

    def test_num_connections(self):
        cbs = [Mock() for _ in range(5)]

        assert self.event.num_connections == 0

        # Track `num_connections` as handlers are connected.
        for i, cb in enumerate(cbs):
            self.event.connect(cb)
            assert self.event.num_connections == i + 1

        # Track `num_connections` as handlers are disconnected.
        for i, cb in enumerate(cbs):
            self.event.disconnect_by_func(cb)
            assert self.event.num_connections == len(cbs) - i - 1
