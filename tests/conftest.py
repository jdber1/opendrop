import asyncio

from gi.repository import Gtk

from opendrop.app.Application import Application
from opendrop.app.GtkHookLoopPolicy import GtkHookLoopPolicy

import pytest

from functools import partial


def pytest_runtest_setup(item: pytest.Item):
    if item.get_marker('gloop') or item.get_marker('gloop_application'):
        item.obj = wrap(item)


def wrap(item):
    func = item.obj

    def wrapper(**kwargs):
        asyncio.set_event_loop_policy(GtkHookLoopPolicy())

        loop = asyncio.get_event_loop()

        err = None

        if item.get_marker('gloop_application'):
            app = item.funcargs['app']

            start = app.run
            stop = partial(Gtk.Application.quit, app)
        else:
            start = Gtk.main
            stop = Gtk.main_quit

        def setup():
            loop.create_task(func(**kwargs)).add_done_callback(teardown)

        def teardown(fut):
            nonlocal err

            err = fut.exception()

            loop.stop()
            stop()

            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

        loop.call_soon(setup)

        loop.run_forever()
        start()

        if err:
            raise err

    return wrapper


@pytest.fixture
def app():
    return Application()
