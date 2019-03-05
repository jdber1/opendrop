import functools
from typing import MutableMapping, Optional, Callable
from typing import Sequence, Tuple, TypeVar, Generic

from gi.repository import Gtk, Gdk, GObject

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import Bindable, AccessorBindable

TaskType = TypeVar('TaskType')


class TasksSidebarView(Generic[TaskType], GtkWidgetView[Gtk.Box]):
    STYLE = '''
    .wizard-sidebar {
        background-color: GAINSBORO;
        border-right: 1px solid SILVER;
        padding: 15px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self, name_from_task: Callable[[TaskType], str]):
        self._name_from_task = name_from_task

        self._active_task_name = None  # type: Optional[str]
        self._task_name_to_lbl = {}  # type: MutableMapping[str, Gtk.Label]
        self.bn_active_task = AccessorBindable(setter=self._set_active_task)

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, vexpand=True)
        self.widget.get_style_context().add_class('wizard-sidebar')
        self.widget.show_all()

    def add_task(self, task: TaskType) -> None:
        task_name = self._name_from_task(task)
        lbl = self._new_label(task_name)
        lbl.show()
        self.widget.add(lbl)
        self._task_name_to_lbl[task_name] = lbl

    def clear(self) -> None:
        for lbl in self._task_name_to_lbl.values():
            lbl.destroy()

        self._task_name_to_lbl = {}
        self._active_task_name = None

    def _set_active_task(self, task: Optional[TaskType]) -> None:
        task_name = self._name_from_task(task)

        old_task_name = self._active_task_name

        if old_task_name is not None:
            old_lbl = self._task_name_to_lbl[old_task_name]
            self._format_label_inactive(old_lbl, old_task_name)

        if task_name is not None:
            lbl = self._task_name_to_lbl[task_name]
            self._format_label_active(lbl, task_name)

        self._active_task_name = task_name

    # todo: the next three methods are not very object oriented.
    def _new_label(self, text: str) -> Gtk.Widget:
        lbl = Gtk.Label(label=text, xalign=0)

        # Set the size request of the label to its maximum possible size when inactive/active, this should stop the
        # sidebar from resizing its width when the largest child label becomes inactive/active.
        self._format_label_active(lbl, text)
        max_width = lbl.get_layout().get_size().width/1000
        self._format_label_inactive(lbl, text)
        max_width = max(max_width, lbl.get_layout().get_size().width/1000)

        lbl.set_size_request(int(max_width + 1), -1)

        return lbl

    @staticmethod
    def _format_label_active(lbl: Gtk.Label, text: str) -> None:
        lbl.set_markup('<b>{}</b>'.format(GObject.markup_escape_text(text)))

    @staticmethod
    def _format_label_inactive(lbl: Gtk.Label, text: str) -> None:
        lbl.set_markup(GObject.markup_escape_text(text))


class TasksSidebarPresenter(Generic[TaskType]):
    def __init__(self, task_and_is_active: Sequence[Tuple[TaskType, Bindable[bool]]], view: TasksSidebarView) \
            -> None:
        self._view = view
        self.__event_connections = []

        self._view.clear()

        for task, is_active in task_and_is_active:
            view.add_task(task)
            is_active.on_changed.connect(functools.partial(self._hdl_task_is_active_changed, task, is_active),
                                         weak_ref=False)
            self._hdl_task_is_active_changed(task, is_active)

    def _hdl_task_is_active_changed(self, task: TaskType, is_active: Bindable[bool]) -> None:
        if is_active.get():
            self._view.bn_active_task.set(task)

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
