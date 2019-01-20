from enum import Enum
from typing import Optional, Callable

from gi.repository import Gtk, Gdk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.events import Event


class YesNoDialogResponse(Enum):
    YES = 0
    NO = 1
    CLOSE = 2


class YesNoDialogView(GtkWidgetView[Gtk.Dialog]):
    def __init__(self, message: str, window: Optional[Gtk.Window]) -> None:
        self.widget = Gtk.MessageDialog(
            parent=window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format=message)
        self.widget.show()

        # Add a reference to self in the widget, otherwise self gets garbage collected for some reason.
        self.widget.__ref_to_view = self

        # Wiring things up

        self.on_response = Event()

        self.widget.connect('response', self._hdl_widget_response)
        self.widget.connect('delete-event', self._hdl_widget_delete_event)
        self.widget.connect('destroy', self._hdl_widget_destroy)

    def _hdl_widget_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        if response == Gtk.ResponseType.YES:
            self.on_response.fire(YesNoDialogResponse.YES)
        elif response == Gtk.ResponseType.NO:
            self.on_response.fire(YesNoDialogResponse.NO)
        elif response == Gtk.ResponseType.DELETE_EVENT:
            self.on_response.fire(YesNoDialogResponse.CLOSE)
        else:
            raise ValueError('Unrecognised response {}'.format(format))

    def _hdl_widget_delete_event(self, widget: Gtk.Dialog, event: Gdk.Event) -> bool:
        # return True to block the dialog from closing.
        return True

    def _hdl_widget_destroy(self, widget: Gtk.Dialog) -> None:
        self.widget.emit('response', Gtk.ResponseType.DELETE_EVENT)

    def destroy(self) -> None:
        self.widget.destroy()


class YesNoDialogPresenter:
    def __init__(self, yes_action: Callable, no_action: Callable, view: YesNoDialogView) -> None:
        self._yes_action = yes_action
        self._no_action = no_action
        self._view = view
        self.__destroyed = False
        self.__cleanup_tasks = []

        event_connections = [
            self._view.on_response.connect(self._hdl_view_response)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def _hdl_view_response(self, response: YesNoDialogResponse) -> None:
        if response is YesNoDialogResponse.YES:
            self._yes_action()
        else:
            self._no_action()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
