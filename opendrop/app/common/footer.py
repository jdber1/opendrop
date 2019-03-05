import asyncio
import math
import time
from enum import Enum
from typing import Optional, Callable

from gi.repository import Gtk, Gdk, GObject

from opendrop.app.common.model.operation import Operation
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.events import Event
from opendrop.utility.simplebindable import AccessorBindable
from opendrop.utility.simplebindablegext import GObjectPropertyBindable


class OperationFooterStatus(Enum):
        IN_PROGRESS = 0
        FINISHED = 1
        CANCELLED = 2


class OperationFooterModel:
    def __init__(self,
                 operation: Operation,
                 back_action: Callable,
                 cancel_action: Callable,
                 save_action: Callable) -> None:
        self._operation = operation
        self.__destroyed = False
        self.__cleanup_tasks = []

        self.bn_status = AccessorBindable(getter=lambda: self.status)
        self.bn_time_start = operation.bn_time_start
        self.bn_time_est_complete = operation.bn_time_est_complete
        self.bn_progress_fraction = operation.bn_progress

        self._back_action = back_action
        self._cancel_action = cancel_action
        self._save_action = save_action

        event_connections = [
            operation.bn_progress.on_changed.connect(self.bn_status.poke),
            operation.bn_done.on_changed.connect(self.bn_status.poke),
            operation.bn_cancelled.on_changed.connect(self.bn_status.poke)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def back(self) -> None:
        self._back_action()

    def cancel(self) -> None:
        self._cancel_action()

    def save(self) -> None:
        self._save_action()

    @property
    def status(self) -> OperationFooterStatus:
        cancelled = self._operation.bn_cancelled.get()
        if cancelled:
            return OperationFooterStatus.CANCELLED

        is_done = self._operation.bn_done.get()
        if is_done:
            return OperationFooterStatus.FINISHED

        return OperationFooterStatus.IN_PROGRESS

    @property
    def time_start(self) -> float:
        return self.bn_time_start.get()

    @property
    def time_est_complete(self) -> float:
        return self.bn_time_est_complete.get()

    @property
    def progress_fraction(self) -> float:
        return self.bn_progress_fraction.get()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class OperationFooterPresenter:
    def __init__(self, model: OperationFooterModel, view: 'OperationFooterView') -> None:
        self._loop = asyncio.get_event_loop()
        self._model = model
        self._view = view
        self.__destroyed = False
        self.__cleanup_tasks = []

        data_bindings = [
            self._model.bn_status.bind_to(self._view.bn_status),
            self._model.bn_progress_fraction.bind_to(self._view.progress.bn_fraction)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            self._model.bn_time_start.on_changed.connect(self._update_view_time),
            self._model.bn_time_est_complete.on_changed.connect(self._update_view_time),
            self._view.on_back_btn_clicked.connect(self._model.back),
            self._view.on_cancel_btn_clicked.connect(self._model.cancel),
            self._view.on_save_btn_clicked.connect(self._model.save)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self._update_view_time_timer_handle = None  # type: Optional[asyncio.TimerHandle]
        self._update_view_time()

    def _update_view_time(self) -> None:
        if self._update_view_time_timer_handle is not None:
            self._update_view_time_timer_handle.cancel()

        if self._model.status is not OperationFooterStatus.IN_PROGRESS:
            return

        time_start = self._model.time_start
        time_est_complete = self._model.time_est_complete
        now = time.time()
        time_elapsed = now - time_start
        time_remaining = time_est_complete - now

        self._view.progress.bn_time_elapsed.set(time_elapsed)

        if time_remaining > 0:
            self._view.progress.bn_time_remaining_visible.set(True)
            self._view.progress.bn_time_remaining.set(time_remaining)
        else:
            self._view.progress.bn_time_remaining_visible.set(False)

        self._update_view_time_timer_handle = self._loop.call_later(1, self._update_view_time)

    def destroy(self) -> None:
        assert not self.__destroyed

        if self._update_view_time_timer_handle is not None:
            self._update_view_time_timer_handle.cancel()

        for f in self.__cleanup_tasks:
            f()

        self.__destroyed = True


class OperationFooterView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .operation-footer-nav-btn {
         min-height: 0px;
         min-width: 60px;
         padding: 0px 4px 0px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class ProgressView(GtkWidgetView[Gtk.Grid]):
        def __init__(self) -> None:
            self.widget = Gtk.Grid(row_spacing=5)
            progress_bar = Gtk.ProgressBar(margin_top=5, hexpand=True, fraction=0.222)
            self.widget.attach(progress_bar, 0, 0, 3, 1)

            self._time_elapsed_lbl = Gtk.Label(xalign=0)
            self._progress_fraction_lbl = Gtk.Label(xalign=0.5, hexpand=True)
            self._time_remaining_lbl = Gtk.Label(xalign=1)
            self._complete_lbl = Gtk.Label(xalign=0.5)

            self.widget.attach(self._time_elapsed_lbl, 0, 1, 1, 1)
            self.widget.attach(self._progress_fraction_lbl, 0, 1, 3, 1)
            self.widget.attach(self._time_remaining_lbl, 2, 1, 1, 1)
            self.widget.attach(self._complete_lbl, 0, 1, 3, 1)

            self.widget.show_all()

            # Wiring things up

            progress_bar.bind_property(
                'fraction',  # source_property
                self._progress_fraction_lbl, 'label',  # target, target_property
                GObject.BindingFlags.SYNC_CREATE,  # flags
                lambda _, v: '{:.0%}'.format(v))  # transform_to

            self.bn_fraction = GObjectPropertyBindable(progress_bar, 'fraction')
            self.bn_time_elapsed = AccessorBindable(setter=self._set_time_elapsed)
            self.bn_time_remaining = AccessorBindable(setter=self._set_time_remaining)
            self.bn_time_remaining_visible = GObjectPropertyBindable(self._time_remaining_lbl, 'visible')

        def _set_time_elapsed(self, seconds: float) -> None:
            self._time_elapsed_lbl.props.label = 'Elapsed: {}'.format(pretty_time(seconds))

        def _set_time_remaining(self, seconds: float) -> None:
            self._time_remaining_lbl.props.label = 'Remaining: {}'.format(pretty_time(seconds))

        def _set_status(self, status: OperationFooterStatus) -> None:
            is_done = status is not OperationFooterStatus.IN_PROGRESS

            if is_done:
                self._complete_lbl.show()
                self._time_elapsed_lbl.show()
                self._time_remaining_lbl.hide()
                self._progress_fraction_lbl.hide()
            else:
                self._complete_lbl.hide()
                self._time_elapsed_lbl.show()
                self._time_remaining_lbl.show()
                self._progress_fraction_lbl.show()

            if status is OperationFooterStatus.FINISHED:
                self._complete_lbl.props.label = 'Finished'
            elif status is OperationFooterStatus.CANCELLED:
                self._complete_lbl.props.label = 'Cancelled'

    def __init__(self) -> None:
        self.widget = Gtk.Grid(margin=10, column_spacing=10, vexpand=False)

        self._cancel_or_back_stack = Gtk.Stack()
        self.widget.attach(self._cancel_or_back_stack, 0, 0, 1, 1)

        self._cancel_btn = Gtk.Button(hexpand=False, vexpand=True)
        self._cancel_btn.get_style_context().add_class('operation-footer-nav-btn')
        self._cancel_or_back_stack.add(self._cancel_btn)

        cancel_btn_inner = Gtk.Grid()
        self._cancel_btn.add(cancel_btn_inner)
        cancel_btn_image = Gtk.Image.new_from_icon_name('process-stop', Gtk.IconSize.BUTTON)
        cancel_btn_lbl = Gtk.Label('Cancel', halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, hexpand=True,
                                   vexpand=True)
        cancel_btn_inner.add(cancel_btn_image)
        cancel_btn_inner.add(cancel_btn_lbl)

        self._back_btn = Gtk.Button('< Back', hexpand=False, vexpand=True)
        self._back_btn.get_style_context().add_class('operation-footer-nav-btn')
        self._cancel_or_back_stack.add(self._back_btn)

        self.progress = self.ProgressView()
        self.widget.attach(self.progress.widget, 1, 0, 1, 1)

        self._save_btn = Gtk.Button(hexpand=False, vexpand=True)
        self._save_btn.get_style_context().add_class('operation-footer-nav-btn')
        self.widget.attach(self._save_btn, 2, 0, 1, 1)

        save_btn_inner = Gtk.Grid()
        self._save_btn.add(save_btn_inner)
        save_btn_image = Gtk.Image.new_from_icon_name('document-save', Gtk.IconSize.BUTTON)
        save_btn_lbl = Gtk.Label('Save', halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, hexpand=True, vexpand=True)
        save_btn_inner.add(save_btn_image)
        save_btn_inner.add(save_btn_lbl)

        self.widget.show_all()

        # Wiring things up

        self.on_back_btn_clicked = Event()
        self.on_cancel_btn_clicked = Event()
        self.on_save_btn_clicked = Event()

        self._back_btn.connect('clicked', lambda *_: self.on_back_btn_clicked.fire())
        self._cancel_btn.connect('clicked', lambda *_: self.on_cancel_btn_clicked.fire())
        self._save_btn.connect('clicked', lambda *_: self.on_save_btn_clicked.fire())

        self.bn_status = AccessorBindable(setter=self._set_status)

    def _set_status(self, status: OperationFooterStatus) -> None:
        self.progress._set_status(status)

        is_done = status is not OperationFooterStatus.IN_PROGRESS
        if is_done:
            self._cancel_or_back_stack.props.visible_child = self._back_btn
            self._save_btn.props.sensitive = True
        else:
            self._cancel_or_back_stack.props.visible_child = self._cancel_btn
            self._save_btn.props.sensitive = False


class LinearNavigatorFooterPresenter:
    def __init__(self, back: Optional[Callable], next: Optional[Callable], view: 'LinearNavigatorFooterView') -> None:
        self._loop = asyncio.get_event_loop()

        self._back = back
        self._next = next

        self._view = view

        self.__event_connections = [
            self._view.on_next_btn_clicked.connect(self._hdl_view_next_btn_clicked),
            self._view.on_back_btn_clicked.connect(self._hdl_view_back_btn_clicked)
        ]

        self._update_view_nav_buttons_visibility()

    def _hdl_view_back_btn_clicked(self) -> None:
        if self._back is None:
            return

        self._back()

    def _hdl_view_next_btn_clicked(self) -> None:
        if self._next is None:
            return

        self._next()

    def _update_view_nav_buttons_visibility(self) -> None:
        self._view.bn_back_btn_visible.set(self._back is not None)
        self._view.bn_next_btn_visible.set(self._next is not None)

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()


class LinearNavigatorFooterView(GtkWidgetView[Gtk.Box]):
    STYLE = '''
    .footer-nav-btn {
         min-height: 0px;
         min-width: 60px;
         padding: 8px 4px 8px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self, back_label: str = '< Back', next_label: str = 'Next >') -> None:
        self.widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=10)
        back_btn = Gtk.Button(back_label)
        back_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_start(back_btn, expand=False, fill=False, padding=0)

        next_btn = Gtk.Button(next_label)
        next_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_end(next_btn, expand=False, fill=False, padding=0)
        self.widget.show_all()

        self.on_next_btn_clicked = Event()
        next_btn.connect('clicked', lambda *_: self.on_next_btn_clicked.fire())

        self.on_back_btn_clicked = Event()
        back_btn.connect('clicked', lambda *_: self.on_back_btn_clicked.fire())

        self.bn_back_btn_visible = GObjectPropertyBindable(back_btn, 'visible')
        self.bn_next_btn_visible = GObjectPropertyBindable(next_btn, 'visible')


# Helper functions

def pretty_time(seconds: float) -> str:
    if not math.isfinite(seconds):
        return ''

    seconds = round(seconds)

    s = seconds % 60
    seconds //= 60
    m = seconds % 60
    seconds //= 60
    h = seconds

    return '{h:0>2}:{m:0>2}:{s:0>2}'.format(h=h, m=m, s=s)
