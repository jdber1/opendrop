from opendrop.shims import tkinter_ as tk

import opendrop.utility.coroutines as coroutines
from opendrop.utility.events import EventsManager
from opendrop.utility.vectors import Vector2

from collections import namedtuple

class ResolutionTuple(Vector2):
    def __repr__(self):
        return "{0}({x}, {y})".format(self.__class__.__name__, x=self.x, y=self.y)

    def __str__(self):
        return "{x}px {y}px".format(x=self.x, y=self.y)

class ViewManager(object):
    def __init__(self, default_title = None):
        self.root = tk.Tk()
        self.events = EventsManager()
        self.current_view = None

        self.default_title = default_title

        self.root.protocol("WM_DELETE_WINDOW", self.exit)

    @property
    def screen_resolution(self):
        return ResolutionTuple(self.root.winfo_screenwidth(), self.root.winfo_screenheight())

    def mainloop(self):
        self.root.mainloop()

    @coroutines.co
    def set_view(self, view, **passthrough_kwargs):
        yield self.clear_view(silent = True)

        new_view = view(self, passthrough_kwargs)

        self.current_view = new_view

        self.events.view_change.fire(new_view)

        yield new_view

    @coroutines.co
    def clear_view(self, silent = False):
        # clear the window
        if self.current_view:
            self.current_view.clear()
            yield self.current_view.core_events.view_cleared

        self.current_view = None

        if not silent:
            self.events.view_change(None)

        self.reset_root()

    def reset_root(self):
        if self.default_title:
            self.root.title(self.default_title)

        self.root.configure(padx=0, pady=0)

    @coroutines.co
    def exit(self):
        yield self.clear_view()
        self.root.destroy()
