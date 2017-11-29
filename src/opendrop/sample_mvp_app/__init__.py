import sys

import gi

gi.require_version('Gtk', '3.0')

from opendrop.sample_mvp_app.SampleApplication import SampleApplication


def main() -> None:
    app = SampleApplication()
    app.run(sys.argv)

    print("Done.")


if __name__ == "__main__":
    main()
