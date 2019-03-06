from gi.repository import Gtk, Gdk

from opendrop.app.ift.model.phys_params import IFTPhysicalParametersFactory
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindablegext import GObjectPropertyBindable, GWidgetStyleClassBindable
from opendrop.utility.validation import FieldPresenter, FieldView, message_from_flags
from opendrop.widgets.float_entry import FloatEntry


class IFTPhysicalParametersFormPresenter:
    def __init__(self, phys_params: IFTPhysicalParametersFactory, view: 'IFTPhysicalParametersFormView') -> None:
        self._phys_params = phys_params
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._field_presenters = [
            FieldPresenter(
                value=self._phys_params.bn_inner_density,
                errors=self._phys_params.inner_density_err,
                field_view=self._view.inner_density_field),
            FieldPresenter(
                value=self._phys_params.bn_outer_density,
                errors=self._phys_params.outer_density_err,
                field_view=self._view.outer_density_field),
            FieldPresenter(
                value=self._phys_params.bn_needle_width,
                errors=self._phys_params.needle_width_err,
                field_view=self._view.needle_width_field),
            FieldPresenter(
                value=self._phys_params.bn_gravity,
                errors=self._phys_params.gravity_err,
                field_view=self._view.gravity_field)]
        self.__cleanup_tasks.extend(fp.destroy for fp in self._field_presenters)

    def validate(self) -> bool:
        for fp in self._field_presenters:
            fp.show_errors()
        return not self._phys_params.has_errors

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class IFTPhysicalParametersFormView(GtkWidgetView[Gtk.Grid]):
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

        # Fields
        self.inner_density_field = FieldView(
            value=GObjectPropertyBindable(self._inner_density_inp, 'value'))
        self.outer_density_field = FieldView(
            value=GObjectPropertyBindable(self._outer_density_inp, 'value'))
        self.needle_width_field = FieldView(
            value=GObjectPropertyBindable(self._needle_width_inp, 'value',
            transform_to=lambda x: x * 1e3 if x is not None else None,
            transform_from=lambda x: x / 1e3 if x is not None else None))
        self.gravity_field = FieldView(
            value=GObjectPropertyBindable(self._gravity_inp, 'value'))

        self._inner_density_inp.connect(
            'focus-out-event', lambda *_: self.inner_density_field.on_user_finished_editing.fire())
        self._outer_density_inp.connect(
            'focus-out-event', lambda *_: self.outer_density_field.on_user_finished_editing.fire())
        self._needle_width_inp.connect(
            'focus-out-event', lambda *_: self.needle_width_field.on_user_finished_editing.fire())
        self._gravity_inp.connect(
            'focus-out-event', lambda *_: self.gravity_field.on_user_finished_editing.fire())

        # Error highlighting
        self.inner_density_field.__refs = [
            GWidgetStyleClassBindable(self._inner_density_inp, 'error').bind_from(
                self.inner_density_field.errors_out),
            GObjectPropertyBindable(self._inner_density_err_msg_lbl, 'label').bind_from(
                message_from_flags('Inner density', self.inner_density_field.errors_out))]
        self.outer_density_field.__refs = [
            GWidgetStyleClassBindable(self._outer_density_inp, 'error').bind_from(
                self.outer_density_field.errors_out),
            GObjectPropertyBindable(self._outer_density_err_msg_lbl, 'label').bind_from(
                message_from_flags('Outer density', self.outer_density_field.errors_out))]
        self.needle_width_field.__refs = [
            GWidgetStyleClassBindable(self._needle_width_inp, 'error').bind_from(
                self.needle_width_field.errors_out),
            GObjectPropertyBindable(self._needle_width_err_msg_lbl, 'label').bind_from(
                message_from_flags('Needle width', self.needle_width_field.errors_out))]
        self.gravity_field.__refs = [
            GWidgetStyleClassBindable(self._gravity_inp, 'error').bind_from(
                self.gravity_field.errors_out),
            GObjectPropertyBindable(self._gravity_err_msg_lbl, 'label').bind_from(
                message_from_flags('Gravity', self.gravity_field.errors_out))]
