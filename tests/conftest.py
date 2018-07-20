import asyncio

import gi
import pytest

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from opendrop.gtk_specific.GtkHookLoopPolicy import GtkHookLoopPolicy


def pytest_runtest_setup(item: pytest.Item):
    if item.get_marker('gloop'):
        item.obj = wrap(item)


def wrap(item):
    func = item.obj

    def wrapper(**kwargs):
        # Set up the wrapped event loop
        original_loop_policy = asyncio.get_event_loop_policy()
        original_loop = asyncio.get_event_loop()

        asyncio.set_event_loop_policy(GtkHookLoopPolicy())
        asyncio.set_event_loop(asyncio.new_event_loop())

        loop = asyncio.get_event_loop()

        start = Gtk.main
        stop = Gtk.main_quit

        err = None

        def setup():
            loop.create_task(func(**kwargs)).add_done_callback(teardown)

        def teardown(fut):
            nonlocal err

            err = fut.exception()

            loop.stop()
            stop()

        loop.call_soon(setup)

        loop.run_forever()
        start()

        if err:
            raise err

        # Restore the original event loop
        asyncio.set_event_loop_policy(original_loop_policy)
        asyncio.set_event_loop(original_loop)

    return wrapper
