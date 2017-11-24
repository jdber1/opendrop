import asyncio

import functools

from gi.repository import GObject


class GtkHookLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        loop = WrappedLoopRunOnGLoop(loop)

        return super().set_event_loop(loop)

    def get_event_loop(self):
        loop = super().get_event_loop()

        assert isinstance(loop, WrappedLoopRunOnGLoop)

        return loop


class WrappedLoopRunOnGLoopMethods:
    def run_forever(self):
        if self.alive:
            raise RuntimeError('This event loop is already running')

        self.alive = True
        GObject.idle_add(self.step)

    def stop(self):
        self.alive = False
        self.step()

    def run_once(self):
        # This pairing of 'arrange a call to stop' and 'run_forever' is used to iterate through the event loop once
        self.target.stop()

        try:
            self.target.run_forever()
        except RuntimeError:
            pass

    def step(self):
        if self.is_closed():
            return

        if self.alive:
            self.call_soon(GObject.idle_add, self.step)
            self.run_once()
        else:
            self.target.stop()


class WrappedLoopRunOnGLoop(asyncio.AbstractEventLoop):
    def __init__(self, target):
        self.target = target
        self.alive = False

    def __getattribute__(self, item):
        if item == "alive" or item == "target":
            return object.__getattribute__(self, item)

        try:
            return functools.partial(getattr(WrappedLoopRunOnGLoopMethods, item), self)
        except AttributeError:
            return getattr(self.target, item)