from typing_extensions import Protocol

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.switch import Switch


class Component(Protocol):
    view = None  # type: GtkWidgetView

    def activate(self):
        pass

    def deactivate(self):
        pass


class Page:
    def __init__(self, name: str, control_switch: Switch, content: Component, footer: Component):
        self.name = name
        self.control_switch = control_switch

        self._content = content
        self._footer = footer

        self.control_switch.on_turned_on.connect(self._activate, immediate=True)
        self.control_switch.on_turned_off.connect(self._deactivate, immediate=True)

    def _activate(self) -> None:
        self._content.activate()
        self._footer.activate()

    def _deactivate(self) -> None:
        self._content.deactivate()
        self._footer.deactivate()

    @property
    def content_view(self) -> GtkWidgetView:
        return self._content.view

    @property
    def footer_view(self) -> GtkWidgetView:
        return self._footer.view
