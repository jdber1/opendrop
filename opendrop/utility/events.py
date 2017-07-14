import functools
import threading
import timeit

class Binding(object):
    def __init__(self, event, listener, num_calls=None):
        self.event = event
        self.listener = listener
        self.remaining = num_calls

        # self.no_modify = threading.Lock() # Not used at the moment

        self._bound = True

    @property
    def remaining(self):
        if self._remaining is None:
            return float("inf")
        else:
            return self._remaining

    @remaining.setter
    def remaining(self, v):
        self._remaining = v

    def unbind(self):
        if self._bound:
            self.event.unbind(self.listener)

class Event(object):
    def __init__(self):
        self.listeners = {}

    def _fire_from_binding(self, binding, *args, **kwargs):
        if binding.remaining:
            binding.remaining -= 1

            if binding.remaining == 0:
                binding.unbind()

            binding.listener(*args, **kwargs)

    def fire(self, *args, **kwargs):
        for listener, binding in list(self.listeners.items()):
            # Need to check if listener is still bound since the previous listeners that were called
            # may have unbounded them
            if binding._bound:
                self._fire_from_binding(binding, *args, **kwargs)

    __call__ = fire

    def bind(self, listener, num_calls=None):
        binding = Binding(self, listener, num_calls)

        self.listeners[listener] = binding

        return binding

    def bind_once(self, listener):
        return self.bind(listener, num_calls=1)

    def unbind(self, listener):
        if listener not in self.listeners:
            raise ValueError(
                "Listener {} is not bound to the event".format(listener)
            )

        binding = self.listeners[listener]

        binding._bound = False
        del self.listeners[listener]

    def unbind_all(self):
        for binding in list(self.listeners.values()):
            binding.unbind()

    def __del__(self):
        self.unbind_all()

class PersistentEvent(Event):
    """
        Similar to an Event but can be 'set' or 'unset', when a PersistentEvent is 'set', any
        current and new listeners bound to the event will be fired with the arguments passed to
        'set'.

        Motive for this class is to be used in AsyncReply.on_reply, where if a new listener binds
        to the event after it has already been replied to, it will miss the reply.

        StateEvent has no .fire() method, use .set() instead to fire listeners. If StateEvent is
        'unset' then 'set', this will re-fire all listeners with the new set of arguments. If
        StateEvent is 'set' while already set, it will also re-fire all listeners.

        Attributes:
            None

        Methods:
            is_set(): Returns True if object has been '.set()', False otherwise or been '.unset()'
            set(*args, **kwargs): 'Sets' the object with arguments *args, **kwargs, new listeners
                will be fired with these arguments until object is .unset()
            bind(listener): Bind a new listener onto the object
    """
    def __init__(self):
        super(PersistentEvent, self).__init__()

        self._set = False

        self._args = []
        self._kwargs = {}

    def is_set(self):
        return self._set

    def set(self, *args, **kwargs):
        self._set = True

        self._args = args
        self._kwargs = kwargs

        self._fire(*args, **kwargs)

    __call__ = set

    def unset(self):
        self._set = False

    def fire(self, *args, **kwargs):
        raise ValueError(
            "Can't manually fire a PersistentEvent, use .set() instead"
        )

    # Make .fire() a private method so it can't be accidentally called
    def _fire(self, *args, **kwargs):
        return super(PersistentEvent, self).fire(*args, **kwargs)

    def bind(self, listener, num_calls=None):
        binding = super(PersistentEvent, self).bind(listener, num_calls)

        if self.is_set():
            self._fire_from_binding(binding, *self._args, **self._kwargs)

        return binding

class WaitLock(PersistentEvent):
    """
        WaitLock, can be locked or unlocked, useful for pausing coroutines until necessary
        conditions.

        Inherits from PersistentEvent, listeners can be bound to WaitLock and will be fired with
        no arguments when unlocked with .unlock(). When .lock() is called, all listeners are unbind.

        Can also set 'min_wait' which specifies the minimum amount of time in seconds that the
        WaitLock must stay locked for before unlocking. 'min_wait' can be configured before or after
        instantiation, e.g.

            wait_lock = WaitLock()

            wait_lock(min_wait=2)

        Will work since the __call__ magic method binds to the class configuration method. Cannot
        set a 'min_wait' lower than what is currently set.
    """
    def __init__(self, **opts):
        super(WaitLock, self).__init__()

        self.start_time = timeit.default_timer()

        self.min_wait = 0
        self.future_unlock_timer = None

        self.configure(**opts)

    def configure(self, **opts):
        if "min_wait" in opts:
            self.min_wait_update(opts["min_wait"])

        return self

    __call__ = configure

    # Changes the min_wait parameter, will lock if already unlocked and unbind all current listeners
    def min_wait_update(self, min_wait):
        if min_wait < self.min_wait:
            raise ValueError(
                "Can't set a lower min_wait of {0}, current min_wait is {1}"
                .format(min_wait, self.min_wait)
            )

        if not self.is_locked():
            elapsed_time = timeit.default_timer() - self.start_time
            if min_wait > elapsed_time:
                self.lock()

                # Since locking resets the start_time back to 0, set min_wait to be how much time
                # left is needed to wait
                self.min_wait = min_wait - elapsed_time

                self.unlock_after(self.min_wait)

        self.min_wait = min_wait

    def is_locked(self):
        return not self.is_set()

    def lock(self):
        # Locking unbinds all current listeners
        self.unbind_all()
        self.unset()

        self.start_time = timeit.default_timer()

    def unlock_after(self, time):
        if self.future_unlock_timer:
            self.future_unlock_timer.cancel()

        self.future_unlock_timer = threading.Timer(time, lambda: self.unlock())
        self.future_unlock_timer.start()

    def unlock(self):
        elapsed_time = timeit.default_timer() - self.start_time
        if self.is_locked():
            if elapsed_time > self.min_wait:
                self.set()
            else:
                self.unlock_after(self.min_wait - elapsed_time)

# basically a defaultdict at the moment, but might add more functionality in the future, used for
# when an object needs many events or dynamic event names. By default, if no event with specified
# name is accessed, a regular Event() is created

class EventsManager(object):
    def __init__(self, events = None):
        self._events = {}

        self._events["_any"] = Event()

        if events:
            for event_name, event in events.items():
                self.new_event(event_name, event)

    # If no event is specified, default create a reguler Event()
    def new_event(self, event_name, event = None):
        event = event or Event()
        if event_name in self._events:
            raise ValueError(
                "Event with name {} already exists".format(event_name)
            )

        event.bind(functools.partial(self._any.fire, event_name))

        self._events[event_name] = event

        return event

    def get_event(self, event_name):
        return self._events[event_name]

    def unbind_all(self):
        for name, event in self._events.items():
            event.unbind_all()

    def __getitem__(self, event_name):
        try:
            return self.get_event(event_name)
        except KeyError:
            return self.new_event(event_name)

    def __setitem__(self, event_name, event):
        return self.new_event(event_name, event)

    __getattr__ = __getitem__

    def __setattr__(self, name, v):
        if name[0] == "_":
            super(EventsManager, self).__setattr__(name, v)
        else:
            return self.__setitem__(name, v)
