from typing import Optional

from gi.repository import Gtk, Gdk

from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter, AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.speaker import Speaker
from opendrop.widgets.float_entry import FloatEntry


class IFTPhysicalParametersRootView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }
    
    .error {
        color: red;
        border: 1px solid red;
    }
    
    .error-text {
        color: red;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class ErrorsView:
        def __init__(self, view: 'IFTPhysicalParametersRootView') -> None:
            self._view = view

            self.bn_inner_density_err_msg = AtomicBindableAdapter(
                setter=self._set_inner_density_err_msg)  # type: AtomicBindable[Optional[str]]
            self.bn_outer_density_err_msg = AtomicBindableAdapter(
                setter=self._set_outer_density_err_msg)  # type: AtomicBindable[Optional[str]]
            self.bn_needle_width_err_msg = AtomicBindableAdapter(
                setter=self._set_needle_width_err_msg)  # type: AtomicBindable[Optional[str]]
            self.bn_gravity_err_msg = AtomicBindableAdapter(
                setter=self._set_gravity_err_msg)  # type: AtomicBindable[Optional[str]]

            self.bn_inner_density_touched = AtomicBindableVar(False)
            self.bn_outer_density_touched = AtomicBindableVar(False)
            self.bn_needle_width_touched = AtomicBindableVar(False)
            self.bn_gravity_touched = AtomicBindableVar(False)

            self._view._inner_density_inp.connect(
                'focus-out-event', lambda *_: self.bn_inner_density_touched.set(True))
            self._view._outer_density_inp.connect(
                'focus-out-event', lambda *_: self.bn_outer_density_touched.set(True))
            self._view._needle_width_inp.connect(
                'focus-out-event', lambda *_: self.bn_needle_width_touched.set(True))
            self._view._gravity_inp.connect(
                'focus-out-event', lambda *_: self.bn_gravity_touched.set(True))

        def reset_touches(self) -> None:
            self.bn_inner_density_touched.set(False)
            self.bn_outer_density_touched.set(False)
            self.bn_needle_width_touched.set(False)
            self.bn_gravity_touched.set(False)

        def touch_all(self) -> None:
            self.bn_inner_density_touched.set(True)
            self.bn_outer_density_touched.set(True)
            self.bn_needle_width_touched.set(True)
            self.bn_gravity_touched.set(True)

        def _set_inner_density_err_msg(self, err_msg: Optional[str]) -> None:
            self._view._inner_density_err_msg_lbl.props.label = err_msg

            if err_msg is not None:
                self._view._inner_density_inp.get_style_context().add_class('error')
            else:
                self._view._inner_density_inp.get_style_context().remove_class('error')

        def _set_outer_density_err_msg(self, err_msg: Optional[str]) -> None:
            self._view._outer_density_err_msg_lbl.props.label = err_msg

            if err_msg is not None:
                self._view._outer_density_inp.get_style_context().add_class('error')
            else:
                self._view._outer_density_inp.get_style_context().remove_class('error')

        def _set_needle_width_err_msg(self, err_msg: Optional[str]) -> None:
            self._view._needle_width_err_msg_lbl.props.label = err_msg

            if err_msg is not None:
                self._view._needle_width_inp.get_style_context().add_class('error')
            else:
                self._view._needle_width_inp.get_style_context().remove_class('error')

        def _set_gravity_err_msg(self, err_msg: Optional[str]) -> None:
            self._view._gravity_err_msg_lbl.props.label = err_msg

            if err_msg is not None:
                self._view._gravity_inp.get_style_context().add_class('error')
            else:
                self._view._gravity_inp.get_style_context().remove_class('error')

    def __init__(self) -> None:
        self.widget = Gtk.Grid(margin=20, row_spacing=10, column_spacing=10)

        # Label widgets
        inner_density_lbl = Gtk.Label('Inner density (kg/m³):', xalign=0)
        self.widget.attach(inner_density_lbl, 0, 0, 1, 1)

        outer_density_lbl = Gtk.Label('Outer density (kg/m³):', xalign=0)
        self.widget.attach(outer_density_lbl, 0, 1, 1, 1)

        needle_width_lbl = Gtk.Label('Needle diameter (mm):', xalign=0)
        self.widget.attach(needle_width_lbl, 0, 2, 1, 1)

        gravity_lbl = Gtk.Label('Gravity (m/s²):', xalign=0)
        self.widget.attach(gravity_lbl, 0, 3, 1, 1)

        # Input widgets
        self._inner_density_inp = FloatEntry(lower=0, width_chars=10)
        self._inner_density_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(self._inner_density_inp, inner_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._outer_density_inp = FloatEntry(lower=0, width_chars=10)
        self._outer_density_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(self._outer_density_inp, outer_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._needle_width_inp = FloatEntry(lower=0, width_chars=10)
        self._needle_width_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(self._needle_width_inp, needle_width_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._gravity_inp = FloatEntry(lower=0, width_chars=10)
        self._gravity_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(self._gravity_inp, gravity_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._inner_density_err_msg_lbl = Gtk.Label(xalign=0)
        self._inner_density_err_msg_lbl.get_style_context().add_class('error-text')
        self.widget.attach_next_to(self._inner_density_err_msg_lbl, self._inner_density_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._outer_density_err_msg_lbl = Gtk.Label(xalign=0)
        self._outer_density_err_msg_lbl.get_style_context().add_class('error-text')
        self.widget.attach_next_to(self._outer_density_err_msg_lbl, self._outer_density_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._needle_width_err_msg_lbl = Gtk.Label(xalign=0)
        self._needle_width_err_msg_lbl.get_style_context().add_class('error-text')
        self.widget.attach_next_to(self._needle_width_err_msg_lbl, self._needle_width_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._gravity_err_msg_lbl = Gtk.Label(xalign=0)
        self._gravity_err_msg_lbl.get_style_context().add_class('error-text')
        self.widget.attach_next_to(self._gravity_err_msg_lbl, self._gravity_inp, Gtk.PositionType.RIGHT, 1, 1)

        self.widget.show_all()

        # Bindables
        self.bn_inner_density = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_outer_density = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_needle_width = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_gravity = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]

        link_atomic_bn_adapter_to_g_prop(self.bn_inner_density, self._inner_density_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_outer_density, self._outer_density_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_needle_width, self._needle_width_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_gravity, self._gravity_inp, 'value')

        self.errors_view = self.ErrorsView(self)


class IFTPhysicalParametersRootPresenter:
    class ErrorsPresenter:
        def __init__(self, validator: IFTPhysicalParametersFactory.Validator,
                     view: IFTPhysicalParametersRootView.ErrorsView) -> None:
            self._validator = validator
            self._view = view

            self.__event_connections = [
                self._validator.bn_inner_density_err_msg.on_changed.connect(self._update_errors, immediate=True),
                self._validator.bn_outer_density_err_msg.on_changed.connect(self._update_errors, immediate=True),
                self._validator.bn_needle_width_err_msg.on_changed.connect(self._update_errors, immediate=True),
                self._validator.bn_gravity_err_msg.on_changed.connect(self._update_errors, immediate=True),

                self._view.bn_inner_density_touched.on_changed.connect(self._update_errors, immediate=True),
                self._view.bn_outer_density_touched.on_changed.connect(self._update_errors, immediate=True),
                self._view.bn_needle_width_touched.on_changed.connect(self._update_errors, immediate=True),
                self._view.bn_gravity_touched.on_changed.connect(self._update_errors, immediate=True),
            ]

            self._view.reset_touches()
            self._update_errors()

        def _update_errors(self) -> None:
            inner_density_err_msg = None  # type: Optional[str]
            outer_density_err_msg = None  # type: Optional[str]
            needle_width_err_msg = None  # type: Optional[str]
            gravity_err_msg = None  # type: Optional[str]

            if self._view.bn_inner_density_touched.get():
                inner_density_err_msg = self._validator.bn_inner_density_err_msg.get()

            if self._view.bn_outer_density_touched.get():
                outer_density_err_msg = self._validator.bn_outer_density_err_msg.get()

            if self._view.bn_needle_width_touched.get():
                needle_width_err_msg = self._validator.bn_needle_width_err_msg.get()

            if self._view.bn_gravity_touched.get():
                gravity_err_msg = self._validator.bn_gravity_err_msg.get()

            self._view.bn_inner_density_err_msg.set(inner_density_err_msg)
            self._view.bn_outer_density_err_msg.set(outer_density_err_msg)
            self._view.bn_needle_width_err_msg.set(needle_width_err_msg)
            self._view.bn_gravity_err_msg.set(gravity_err_msg)

        def destroy(self) -> None:
            for ec in self.__event_connections:
                ec.disconnect()

    def __init__(self, phys_params_factory: IFTPhysicalParametersFactory, view: IFTPhysicalParametersRootView) -> None:
        self._errors_presenter = self.ErrorsPresenter(phys_params_factory.validator, view.errors_view)
        self.__data_bindings = [
            Binding(phys_params_factory.bn_inner_density, view.bn_inner_density),
            Binding(phys_params_factory.bn_outer_density, view.bn_outer_density),
            Binding(phys_params_factory.bn_needle_width, view.bn_needle_width),
            Binding(phys_params_factory.bn_gravity, view.bn_gravity)
        ]

    def destroy(self) -> None:
        self._errors_presenter.destroy()

        for db in self.__data_bindings:
            db.unbind()


class IFTPhysicalParametersSpeaker(Speaker):
    def __init__(self, phys_params_factory: IFTPhysicalParametersFactory, content_stack: StackModel) -> None:
        super().__init__()

        self._phys_params_factory = phys_params_factory

        self._content_stack = content_stack

        self._root_view = IFTPhysicalParametersRootView()
        self._root_presenter = None  # type: Optional[IFTPhysicalParametersRootPresenter]

        self._root_view_stack_key = object()
        self._content_stack.add_child(self._root_view_stack_key, self._root_view)

    def do_activate(self) -> None:
        self._root_presenter = IFTPhysicalParametersRootPresenter(
            phys_params_factory=self._phys_params_factory,
            view=self._root_view
        )

        # Make root view visible.
        self._content_stack.visible_child_key = self._root_view_stack_key

    async def do_request_deactivate(self) -> bool:
        is_valid = self._phys_params_factory.validator.check_is_valid()
        if is_valid:
            return False

        self._root_view.errors_view.touch_all()
        return True

    def do_deactivate(self) -> None:
        assert self._root_presenter is not None
        self._root_presenter.destroy()
