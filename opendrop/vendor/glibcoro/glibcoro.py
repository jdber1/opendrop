#+
# glibcoro -- An interface between asyncio and the GLib event loop.
#
# The goal of this project is to implement an interface to the GLib/GTK+
# event loop as a subclass of asyncio.AbstractEventLoop, taking full
# advantage of the coroutine feature available in Python 3.5 and later.
#
# Copyright 2017-2018 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under the GNU Lesser General Public License v2.1 or later.
#-

import sys
import traceback
import time
import threading
import asyncio
import gi
from gi.repository import \
    GLib

def _fd_fileno(fd) :
    if hasattr(fd, "fileno") :
        fileno = fd.fileno()
    elif isinstance(fd, int) :
        fileno = fd
    else :
        raise TypeError("fd does not have a fileno")
    #end if
    return \
        fileno
#end _fd_fileno

class TimerHandle(asyncio.TimerHandle) :
    "need to wrap asyncio.TimerHandle with extra info to correctly handle calls" \
    " to GLibEventLoop._timer_handle_cancelled."

    __slots__ = \
        (
            "_glib_source",
            "_triggered",
        )

    def __init__(self, when, callback, args, loop) :
        super().__init__(when, callback, args, loop)
        self._triggered = False
        self._glib_source = None # to begin with
    #end __init__

    def _run(self) :
        self._triggered = True
        super()._run()
    #end _run

#end TimerHandle

class GLibEventLoop(asyncio.AbstractEventLoop) :

    # <https://developer.gnome.org/glib/stable/glib-The-Main-Event-Loop.html>

    __slots__ = \
        (
            "_gloop",
            "_closed",
            "_task_factory",
            "_exception_handler",
            "_reader_sources",
            "_writer_sources",
            "_signal_sources",
        )

    def __init__(self) :
        self._gloop = GLib.MainLoop()
        self._closed = False
        self._task_factory = None
        self._exception_handler = None
        self._reader_sources = {} # indexed by fileno
        self._writer_sources = {} # indexed by fileno
        self._signal_sources = {} # indexed by signum
    #end __init__

    def run_forever(self) :
        self._check_closed()
        self._gloop.run()
    #end run_forever

    def run_until_complete(self, future) :

        result = None

        async def awaitit() :
            nonlocal result
            try :
                result = await future
            except Exception as exc :
                traceback.print_exc()
            #end try
            self.stop()
        #end awaitit

    #begin run_until_complete
        self._check_closed()
        self.create_task(awaitit())
        self.run_forever()
        return \
            result
    #end run_until_complete

    def stop(self) :
        self._gloop.quit()
    #end stop

    def is_running(self) :
        return \
            self._gloop.is_running()
    #end is_running

    def _check_closed(self) :
        if self._closed :
            raise asyncio.InvalidStateError("event loop is closed")
        #end if
    #end _check_closed

    def is_closed(self) :
        return \
            self._closed
    #end is_closed

    def close(self) :
        if self.is_running() :
            raise asyncio.InvalidStateError("event loop cannot be closed while running")
        #end if
        self._closed = True
    #end close

    def _timer_handle_cancelled(self, handle) :
        # called from asyncio.TimerHandle.cancel()
        # sys.stderr.write("cancelling timer %s, one of mine %s, triggered %s\n" % (repr(handle), hasattr(handle, "_glib_source"), getattr(handle, "_triggered", None))) # debug
        if not handle._triggered :
            GLib.source_remove(handle._glib_source)
        #end if
    #end _timer_handle_cancelled

    def get_exception_handler(self) :
        return \
            self._exception_handler
    #end get_exception_handler

    def set_exception_handler(self, handler) :
        if handler != None and not callable(handler) :
            raise TypeError("exception handler must be callable")
        #end if
        self._exception_handler = handler
    #end set_exception_handler

    def call_exception_handler(self, context) :
        handler = self.get_exception_handler()
        if handler == None :
            handler = self.default_exception_handler
        #end if
        handler(context)
    #end call_exception_handler

    def default_exception_handler(self, context) :
        # sys.stderr.write("default_exception_handler: %s\n" % repr(context)) # debug
        # roughly modelled on asyncio.BaseEventLoop.default_exception_handler
        if "message" in context :
            sys.stderr.write(context["message"])
            sys.stderr.write("\n")
        #end if
        for key in sorted(context) :
            if key not in ("exception", "message") :
                sys.stderr.write("%s: %s\n" % (key, context[key]))
            #end if
        #end for
        if "exception" in context :
            exc = context["exception"]
            traceback.print_exception(type(exc), exc, exc.__traceback__)
        #end if
    #end default_exception_handler

    # TODO: shutdown_asyncgens?

    def call_soon(self, callback, *args) :

        def doit(hdl) :
            if not hdl._cancelled :
                hdl._run()
            #end if
            return \
                False # always one-shot
        #end doit

    #begin call_soon
        self._check_closed()
        hdl = asyncio.Handle(callback, args, self)
        GLib.idle_add(doit, hdl)
        self = None # avoid circular references
        return \
            hdl
    #end call_soon

    call_soon_threadsafe = call_soon # GLib is threadsafe

    def _call_timed_common(self, when, callback, args) :

        def doit(hdl) :
            if not hdl._cancelled :
                hdl._run()
            #end if
            return \
                False # always one-shot
        #end doit

    #begin _call_timed_common
        self._check_closed()
        hdl = TimerHandle(when, callback, args, self)
        hdl._glib_source = GLib.timeout_add(max(round((when - self.time()) * 1000), 0), doit, hdl)
        self = None # avoid circular references
        return \
            hdl
    #end _call_timed_common

    def call_later(self, delay, callback, *args) :
        return \
            self._call_timed_common(delay + self.time(), callback, args)
    #end call_later

    def call_at(self, when, callback, *args) :
        return \
            self._call_timed_common(when, callback, args)
    #end call_at

    def time(self) :
        # might as well do same thing as asyncio.BaseEventLoop
        return \
            time.monotonic()
    #end time

    def create_future(self) :
        return \
            asyncio.Future(loop = self)
    #end create_future

    def create_task(self, coro) :
        self._check_closed()
        if self._task_factory != None :
            result = self._task_factory(self, coro)
        else :
            result = asyncio.Task(coro)
              # will call my call_soon routine to schedule itself
        #end if
        return \
            result
    #end create_task

    def get_task_factory(self) :
        return \
            self._task_factory
    #end get_task_factory

    def set_task_factory(self, factory) :
        if factory != None and not callable(factory) :
            raise TypeError("task factory must be callable")
        #end if
        self._task_factory = factory
    #end set_task_factory

    # TODO: threads, executor, network, pipes and subprocesses

    # <https://developer.gnome.org/glib/stable/glib-UNIX-specific-utilities-and-integration.html>

    def _add_source(self, attr, key, source_nr) :
        sources = getattr(self, attr)
        if key not in sources :
            sources[key] = []
        #end if
        sources[key].append(source_nr)
    #end _add_source

    def _remove_sources(self, attr, key) :
        sources = getattr(self, attr)
        if key in sources :
            for source_nr in sources[key] :
                GLib.source_remove(source_nr)
            #end for
            del sources[key]
        #end if
    #end _remove_sources

    def add_reader(self, fd, callback, *args) :

        def doit(_1, _2, _3, _4) : # not sure what the args are
            callback(*args)
            return \
                True # keep watching
        #end doit

    #begin add_reader
        fileno = _fd_fileno(fd)
        self._add_source \
          (
            attr = "_reader_sources",
            key = fileno,
            source_nr = GLib.unix_fd_add_full
              (
                0,
                fileno,
                GLib.IOCondition.IN | GLib.IOCondition.PRI,
                doit,
                None,
                None
              )
          )
        self = None # avoid circular references
    #end add_reader

    def remove_reader(self, fd) :
        self._remove_sources("_reader_sources", _fd_fileno(fd))
    #end remove_reader

    def add_writer(self, fd, callback, *args) :

        def doit(_1, _2, _3, _4) : # not sure what the args are
            callback(*args)
            return \
                True # keep watching
        #end doit

    #begin add_writer
        fileno = _fd_fileno(fd)
        self._add_source \
          (
            attr = "_writer_sources",
            key = fileno,
            source_nr = GLib.unix_fd_add_full
              (
                0,
                fileno,
                GLib.IOCondition.OUT | GLib.IOCondition.PRI,
                doit,
                None,
                None
              )
          )
        self = None # avoid circular references
    #end add_writer

    def remove_writer(self, fd) :
        self._remove_sources("_writer_sources", _fd_fileno(fd))
    #end remove_writer

    # TODO: sockets

    def add_signal_handler(self, signum, callback, *args) :

        def doit(_1, _2) : # not sure what the args are
            callback(*args)
            return \
                True # keep triggering
        #end doit

    #begin add_signal_handler
        self._add_source \
          (
            attr = "_signal_sources",
            key = signum,
            source_nr = GLib.unix_signal_add(0, signum, doit, None, None)
          )
        self = None # avoid circular references
    #end add_signal_handler

    def remove_signal_handler(self, signum) :
        self._remove_sources("_signal_sources", signum)
    #end remove_signal_handler

    # TODO: debug flag

    def get_debug(self) :
        return \
            False
    #end get_debug

#end GLibEventLoop

class GLibChildWatcher(asyncio.AbstractChildWatcher) :
    "watch for termination of child processes. Note that you need to" \
    " spawn the processes with the GLib.SPAWN_DO_NOT_REAP_CHILD flag," \
    " otherwise any handlers registered here for them will not be called."

    # <https://developer.gnome.org/glib/stable/glib-Spawning-Processes.html>

    __slots__ = ("_sources",)

    def __init__(self) :
        self._sources = {}
    #end __init__

    def add_child_handler(self, pid, callback, args) :
        "registers a handler which will be invoked as" \
        " callback(pid, returncode, *args) when the process with ID pid terminates."

        def child_done(pid, status, self) :
            del self._sources[pid]
            callback(pid, status, *args)
        #end child_done

    #begin add_child_handler
        if pid in self._sources :
            self.remove_child_handler(pid)
        #end if
        self._sources[pid] = GLib.child_watch_add(pid, child_done, self)
    #end add_child_handler

    def remove_child_handler(self, pid) :
        "removes any installed handler for the process with ID pid."
        if pid in self._sources :
            GLib.source_remove(self._sources[pid])
            del self._sources[pid]
        #end if
    #end remove_child_handler

    def attach_loop(self, loop) :
        if loop != asyncio.get_event_loop() or not isinstance(loop, GLibEventLoop) :
            raise TypeError("I only support attaching to default GLibEventLoop")
        #end if
    #end attach_loop

    def close(self) :
        pass
    #end close

    # asyncio.unix_events.FastChildWatcher uses context manager
    # calls to keep track of terminations of processes not
    # created by asyncio. Since I assume all process creations
    # are done through GLib, I just implement these as no-ops.

    def __enter__(self) :
        return \
            self
    #end __enter__

    def __exit__(self, exc_type, exc_value, traceback) :
        pass
    #end __exit__

#end GLibChildWatcher

_running_loop = None

class GLibEventLoopPolicy(asyncio.AbstractEventLoopPolicy) :

    __slots__ = ("_child_watcher",)

    def __init__(self) :
        self._child_watcher = None
    #end __init__

    @staticmethod
    def _check_is_main_thread() :
        # prevent use with multiple threads.
        if threading.current_thread() is not threading.main_thread() :
            raise RuntimeError \
              (
                "use on other than main thread is not currently supported"
              )
        #end if
    #end _check_is_main_thread

    def get_event_loop(self) :
        self._check_is_main_thread()
        global _running_loop
        if _running_loop == None :
            _running_loop = self.new_event_loop()
        #end if
        return \
            _running_loop
    #end get_event_loop

    def set_event_loop(self, loop) :
        self._check_is_main_thread()
        if not isinstance(loop, GLibEventLoop) :
            raise TypeError("loop must be a GLibEventLoop")
        #end if
        global _running_loop
        _running_loop = loop
    #end set_event_loop

    def new_event_loop(self) :
        self._check_is_main_thread()
        return \
            GLibEventLoop()
    #end new_event_loop

    def get_child_watcher(self) :
        if self._child_watcher == None :
            self._child_watcher = GLibChildWatcher()
            self._child_watcher.attach_loop(self.get_event_loop())
        #end if
        return \
            self._child_watcher
    #end get_child_watcher

    def set_child_watcher(self, watcher) :
        if not isinstance(watcher, GLibChildWatcher) :
            raise TypeError("watcher is not a GLibChildWatcher")
        #end if
        if self._child_watcher != watcher :
            if self._child_watcher != None :
                self._child_watcher.close()
            #end if
            self._child_watcher = watcher
            self._child_watcher.attach_loop(self.get_event_loop())
        #end if
    #end set_child_watcher

#end GLibEventLoopPolicy

def install() :
    "installs this module as the default purveyor of asyncio event loops."
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
#end install
