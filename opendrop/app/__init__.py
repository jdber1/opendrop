import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from opendrop.app.app import App


def main():
    app = App()
    app.start()


if __name__ == '__main__':
    main()
