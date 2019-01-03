from typing import MutableSequence

import cairo
from gi.repository import Gtk, GObject


class Layer(GObject.GObject):
    def do_draw(self, cr: cairo.Context) -> None:
        pass

    @GObject.Signal
    def request_draw(self) -> None:
        """Let the parent LayeredDrawingArea know that this layer has changed and the widget needs to be redrawn."""


class LayeredDrawingArea(Gtk.DrawingArea):
    def __init__(self, **properties) -> None:
        super().__init__(**properties)
        self._layers = []  # type: MutableSequence[Layer]
        self._pending_draw_layers = []  # type: MutableSequence[Layer]

    def add_layer(self, layer: Layer) -> None:
        self._layers.append(layer)
        layer.connect('request-draw', self._hdl_layer_request_draw)
        self.queue_draw()

    def _hdl_layer_request_draw(self, layer: Layer) -> None:
        if layer in self._pending_draw_layers:
            return

        self.queue_draw()

    def do_draw(self, cr: cairo.Context) -> None:
        self._pending_draw_layers = list(self._layers)
        for layer in self._layers:
            layer.draw(cr)
            self._pending_draw_layers.remove(layer)
