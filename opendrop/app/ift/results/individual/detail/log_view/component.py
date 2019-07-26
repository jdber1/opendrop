from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable

log_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@log_cs.view()
class LogView(View['LogPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.ScrolledWindow()

        self._text_view = Gtk.TextView(
            monospace=True,
            editable=False,
            wrap_mode=Gtk.WrapMode.CHAR,
            hexpand=True,
            vexpand=True,
            margin=10
        )
        self._text_view.show()
        self._widget.add(self._text_view)

        self.presenter.view_ready()

        return self._widget

    def set_log_text(self, text: str) -> None:
        self._text_view.get_buffer().set_text(text)

    def _do_destroy(self) -> None:
        self._widget.destroy()


@log_cs.presenter(options=['in_log_text'])
class LogPresenter(Presenter['LogView']):
    def _do_init(self, in_log_text: Bindable[str]) -> None:
        self._bn_log_text = in_log_text
        self.__event_connections = []

    def view_ready(self):
        self.__event_connections.extend([
            self._bn_log_text.on_changed.connect(
                self._hdl_log_text_changed
            )
        ])

    def _hdl_log_text_changed(self) -> None:
        log_text = self._bn_log_text.get()
        self.view.set_log_text(log_text)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
