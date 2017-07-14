"""
    Really simple implementation of coroutines
"""

import inspect

from opendrop.utility.events import Event, PersistentEvent

import threading

class UniqueVariable:
    pass

# Constants

EXIT = UniqueVariable()

class coroutine(object):
    def __init__(self, gen, root_reply):
        # TODO: if root_reply is fired, stop the coroutine
        # self.alive = True
        self.gen = gen
        self.lock = threading.RLock()

        self.root_reply = root_reply

    def step(self, send_value = None):
        with self.lock:
            try:
                yield_value = self.gen.send(send_value)

                if yield_value == EXIT:
                    raise StopIteration
                elif isinstance(yield_value, tuple) and len(yield_value) and yield_value[0] == EXIT:
                    send_value = yield_value[1:]

                    if len(send_value) == 1:
                        send_value = send_value[0]
                    elif len(send_value) == 0:
                        send_value = None

                    raise StopIteration
                elif isinstance(yield_value, Event):
                    def cb(*args, **kwargs):
                        if len(args) == 1:
                            args = args[0]

                        if kwargs:
                            gen.throw(
                                ValueError,
                                "Can't yield on an event that has been fired with keyword arguments"
                            )
                        #print("Fired {}, continueing...".format(cb))
                        self.step(send_value = args)
                    #print("Binding from... {0} to... {1}".format(cb, yield_value))
                    yield_value.bind_once(cb)
                else:
                    # Didn't yield an Event, do nothing and pass it back
                    self.step(send_value = yield_value)
            except StopIteration:
                self.root_reply(send_value)

def co(function):
    if inspect.isgeneratorfunction(function):
        def wrapper(*args, **kwargs):
            reply = PersistentEvent()
            gen = function(*args, **kwargs)

            coroutine(gen, reply).step()

            return reply
        return wrapper
    else: # Do nothing
        return function
