import asyncio
import warnings

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

import gi
gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gio, GLib, Gtk

import opendrop
from opendrop.vendor import aioglib


# Register application resources.
try:
    resource_data = importlib_resources.read_binary(opendrop, 'data.gresource')
except FileNotFoundError:
    warnings.warn("Failed to load 'data.gresource' file")
else:
    resource = Gio.Resource.new_from_data(GLib.Bytes(resource_data))
    resource._register()


Gtk.IconTheme.get_default().add_resource_path('/opendrop/assets/icons')

# Install custom event loop policy.
asyncio.set_event_loop_policy(aioglib.GLibEventLoopPolicy())


from . import main_menu, ift, conan, common
from .app import OpendropApplication
