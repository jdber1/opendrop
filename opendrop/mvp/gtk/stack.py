from typing import Any, Mapping, Optional

from gi.repository import Gtk

from opendrop.mvp.component import ComponentSymbol, ComponentFactory
from opendrop.mvp.presenter import Presenter
from opendrop.mvp.view import View
from opendrop.utility.bindable import Bindable

stack_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@stack_cs.view(options=['children', 'gtk_properties'])
class StackView(View['StackPresenter', Gtk.Widget]):
    def _do_init(self, children: Mapping[Any, ComponentFactory[Gtk.Widget]],
                 gtk_properties: Optional[Mapping[str, Any]] = None) -> Gtk.Widget:
        self._children = children

        # Active child component id
        self._active_child_cid = None

        # Active child stack id
        self._active_child_sid = None

        self.widget = Gtk.Grid(**(gtk_properties or {}))
        self.widget.show()

        self.presenter.view_ready()

        return self.widget

    def set_active(self, new_child_sid: Any) -> None:
        if self._active_child_sid == new_child_sid: return

        new_child_factory = self._children[new_child_sid] if new_child_sid is not None else None

        if self._active_child_cid:
            self.remove_component(self._active_child_cid)
            self._active_child_cid = None
            self._active_child_sid = None

        if new_child_factory is None: return

        self._active_child_cid, new_child_widget = self.new_component(new_child_factory)
        self._active_child_sid = new_child_sid

        new_child_widget.show()

        self.widget.add(new_child_widget)

    def _do_destroy(self):
        self.widget.destroy()


@stack_cs.presenter(options=['active_stack'])
class StackPresenter(Presenter['StackView']):
    def _do_init(self, active_stack: Bindable) -> None:
        self._active_stack = active_stack
        self.__event_connections = [
            active_stack.on_changed.connect(self._update_view)
        ]

    def view_ready(self) -> None:
        self._update_view()

    def _update_view(self) -> None:
        self.view.set_active(self._active_stack.get())

    def _do_destroy(self) -> None:
        for conn in self.__event_connections:
            conn.disconnect()
