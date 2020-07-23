# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import asyncio
import warnings

import gi
gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gio, GLib, Gtk

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

try:
    from typing import Protocol, Literal
except ImportError:
    import typing
    from typing_extensions import Protocol, Literal
    typing.Protocol = Protocol
    typing.Literal = Literal

from opendrop.metadata import *
from opendrop.vendor import aioglib


# Register application resources.
try:
    resource_data = importlib_resources.read_binary(__spec__.parent, 'data.gresource')
except FileNotFoundError:
    warnings.warn("Failed to load 'data.gresource' file")
else:
    resource = Gio.Resource.new_from_data(GLib.Bytes(resource_data))
    resource._register()


Gtk.IconTheme.get_default().add_resource_path('/opendrop/assets/icons')

# Install custom event loop policy.
asyncio.set_event_loop_policy(aioglib.GLibEventLoopPolicy())
