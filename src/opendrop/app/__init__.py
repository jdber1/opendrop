import sys

import gi

from opendrop.app.app import OpendropApplication

gi.require_version('Gtk', '3.0')


def main() -> None:
    app = OpendropApplication()

    app.run(sys.argv)

    print("Done.")


if __name__ == "__main__":
    main()
