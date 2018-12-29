from typing import Optional

from gi.repository import Gtk, Gdk

from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
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
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

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
        inner_density_inp = FloatEntry(lower=0, width_chars=10)
        inner_density_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(inner_density_inp, inner_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        outer_density_inp = FloatEntry(lower=0, width_chars=10)
        outer_density_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(outer_density_inp, outer_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        needle_width_inp = FloatEntry(lower=0, width_chars=10)
        needle_width_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(needle_width_inp, needle_width_lbl, Gtk.PositionType.RIGHT, 1, 1)

        gravity_inp = FloatEntry(lower=0, width_chars=10)
        gravity_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(gravity_inp, gravity_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self.widget.show_all()

        # Bindables
        self.bn_inner_density = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_outer_density = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_needle_width = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]
        self.bn_gravity = AtomicBindableAdapter()  # type: AtomicBindableAdapter[Optional[float]]

        link_atomic_bn_adapter_to_g_prop(self.bn_inner_density, inner_density_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_outer_density, outer_density_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_needle_width, needle_width_inp, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_gravity, gravity_inp, 'value')


class IFTPhysicalParametersRootPresenter:
    def __init__(self, phys_params_factory: IFTPhysicalParametersFactory, view: IFTPhysicalParametersRootView) -> None:
        self.__data_bindings = [
            Binding(phys_params_factory.bn_inner_density, view.bn_inner_density),
            Binding(phys_params_factory.bn_outer_density, view.bn_outer_density),
            Binding(phys_params_factory.bn_needle_width, view.bn_needle_width),
            Binding(phys_params_factory.bn_gravity, view.bn_gravity)
        ]

    def destroy(self) -> None:
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

    def do_deactivate(self) -> None:
        assert self._root_presenter is not None
        self._root_presenter.destroy()
