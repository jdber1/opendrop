Opendrop Events
===============

Instead of subclassing `GObject` and using custom signals, Opendrop has
its own event class for connecting handlers to events. The `Event` class
uses Python's `asyncio` event loop to schedule the callback of handlers,
this allows it to be more independent from external libraries.

The Opendrop application first sets `GtkHookLoopPolicy` as the event
loop policy to allow the `asyncio` event loop to run alongside the Gtk
main loop (a bit of a hack).

Creating a new `Event` object creates a new event that handlers can
connect to and will be invoked whenever the event is fired (read the
documentation fot `Event` for the options available when connecting
handlers or firing events).

Example (the `asyncio` event loop must be running):

    def callback(arg):
        print('I was called with {}'.format(arg))

    my_event = Event()
    my_event.connect(callback)
    my_event.fire('an apple')

Output:

    I was called with an apple

One implementation detail to note is that when an event is fired, its
connected handlers aren't invoked immediately, but their callback are
arranged with `AbstractEventLoop.call_soon()`, so the following code:

    import asyncio
    from unittest.mock import Mock

    async def main():
        cb = Mock()
        ev = Event()

        ev.connect(cb)
        ev.fire()

        await asyncio.sleep(0)

        cb.assert_called_once_with()

    asyncio.get_event_loop().run_until_complete(main())

Will fail with an `AssertionError` if the await statement is not used.
Handler's aren't invoked 'immediately' when an event is fired to avoid
the possibility of a blocking infinite loop if a handler fires the event
that it's connected to.

If you would like for a handler to be fired immediately, pass the
`immediate=True` keyword argument to the `connect()` method when
connecting the handler.

`immediate=True` can't be used when connecting a coroutine function to
an event (such as functions defined with `async def`), since
coroutines need to be scheduled with `AbstractEventLoop.create_task()`
which will add the coroutine to the event loop queue, hence there is no
way to call it immediately. There could be a way to run the 'first part'
of a coroutine function (before the `await` statement) 'immediately',
but this has not been implemented as there has been no use cases for it.