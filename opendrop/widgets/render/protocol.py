from abc import abstractmethod
from enum import Enum
from typing import Optional, Any

import cairo
from gi.repository import Gdk


class Render:
    class ViewportStretch(Enum):
        FIT = 0
        FILL = 1

    def add_render_object(self, obj: 'RenderObject') -> None:
        pass

    def remove_render_object(self, obj: 'RenderObject') -> None:
        pass

    # Methods to be provided by GObject.Object or Gtk.Widget

    props = None  # type: Any

    @abstractmethod
    def emit(self, *args, **kwargs) -> None:
        """GObject.Object.emit()"""

    @abstractmethod
    def connect(self, *args, **kwargs) -> int:
        """GObject.Object.connect()"""

    @abstractmethod
    def get_window(self, *args, **kwargs) -> Optional[Gdk.Window]:
        """Gtk.Widget.get_window()"""


class RenderObject:
    def __init__(self, **options) -> None:
        super().__init__(**options)

    @abstractmethod
    def set_parent(self, parent: Render) -> None:
        pass

    @abstractmethod
    def draw(self, cr: cairo.Context) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass

    # Methods to be provided by GObject.Object

    @abstractmethod
    def emit(self, *args, **kwargs) -> None:
        """GObject.Object.emit()"""

    @abstractmethod
    def connect(self, *args, **kwargs) -> int:
        """GObject.Object.connect()"""

    @abstractmethod
    def disconnect(self, *args, **kwargs) -> int:
        """GObject.Object.disconnect()"""
