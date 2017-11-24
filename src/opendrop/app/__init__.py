import asyncio
import sys
from typing import Callable

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from opendrop.app.Application import Application
from opendrop.app.GtkHookLoopPolicy import GtkHookLoopPolicy

asyncio.set_event_loop_policy(GtkHookLoopPolicy())


def main():
    app = Application()
    asyncio.get_event_loop().call_later(1, print, "hi")
    asyncio.get_event_loop().run_forever()

    app.on_quit.connect(app.quit)
    app.run(sys.argv)

    print("over")


if __name__ == "__main__":
    main()
