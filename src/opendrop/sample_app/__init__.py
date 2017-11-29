import sys

import gi

gi.require_version('Gtk', '3.0')

from opendrop.sample_app.Application import Application


def main() -> None:
    app = Application()

    app.run(sys.argv)

    print("Done.")


if __name__ == "__main__":
    main()
