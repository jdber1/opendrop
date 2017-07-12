from opendrop.utility.events import PersistentEvent, EventsManager
from opendrop.utility.structs import Struct

import threading

class View(object):
    def __init__(self, view_manager, passthrough_kwargs):

        self.view_manager = view_manager
        self.root = view_manager.root
        self.alive = True
        self.busy = threading.Lock()

        self.events = EventsManager()
        self.core_events = EventsManager({
            "view_cleared": PersistentEvent()
        })

        self.body(**passthrough_kwargs)

    def body(self):
        # build the window
        pass

    def clear(self):
        # Wait to acquire busy lock, don't block since .clear() could be running on the main thread
        # where the Tk .mainloop() is also running on, if the main thread is blocked, program could
        # become unresponsive
        if self.busy.acquire(False) is False:
            self.root.after(0, self.clear)
            return

        # Do view specific clear
        self._clear()

        self.events.unbind_all()

        for child in self.root.winfo_children():
            child.destroy()

        self.alive = False
        self.busy.release()

        self.core_events.view_cleared()

        self.core_events.unbind_all()

    def _clear(self):
        pass

    def center(self):
        self.root.update_idletasks()

        screen_w, screen_h = self.view_manager.screen_resolution
        window_w, window_h = self.root.winfo_width(), self.root.winfo_height()

        x = screen_w/2 - window_w/2
        y = screen_h/2 - window_h/2
        self.root.geometry("{0}x{1}+{2}+{3}".format(window_w, window_h, x, y))
