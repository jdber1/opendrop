import asyncio
import sys

import gi

gi.require_version('Gtk', '3.0')

from opendrop.app.Application import Application
from opendrop.app.GtkHookLoopPolicy import GtkHookLoopPolicy


def main() -> None:
    app = Application()

    asyncio.set_event_loop_policy(GtkHookLoopPolicy())
    asyncio.get_event_loop().run_forever()

    app.connect('on_quit', asyncio.get_event_loop().stop)

    app.run(sys.argv)

    print("Done.")


if __name__ == "__main__":
    main()
