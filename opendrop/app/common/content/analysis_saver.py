from typing import Set

from gi.repository import Gtk, Gdk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import AccessorBindable, apply as bn_apply
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.utility.validation import message_from_flags, add_style_class_when_flags, ValidationFlag, FieldView, \
    FieldPresenter
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry
from ..model.analysis_saver import FigureOptions


class FigureOptionsView(GtkWidgetView[Gtk.Grid]):
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
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self, figure_name: str) -> None:
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self._should_save_figure_inp = Gtk.CheckButton(label='Save {}'.format(figure_name))
        self.widget.add(self._should_save_figure_inp)

        self._more_options = Gtk.Grid(margin_left=30, row_spacing=5, column_spacing=10)
        self.widget.add(self._more_options)

        dpi_lbl = Gtk.Label('Figure DPI:', xalign=0)
        self._more_options.attach(dpi_lbl, 0, 0, 1, 1)

        dpi_inp_ctn = Gtk.Grid()
        self._more_options.attach_next_to(dpi_inp_ctn, dpi_lbl, Gtk.PositionType.RIGHT, 1, 1)
        dpi_inp = IntegerEntry(value=300, lower=72, upper=10000, width_chars=5)
        dpi_inp.get_style_context().add_class('small-pad')
        dpi_inp_ctn.add(dpi_inp)

        dpi_err_lbl = Gtk.Label(xalign=0, width_request=190)
        dpi_err_lbl.get_style_context().add_class('error-text')
        self._more_options.attach_next_to(dpi_err_lbl, dpi_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

        size_lbl = Gtk.Label('Figure size (cm):', xalign=0)
        self._more_options.attach(size_lbl, 0, 1, 1, 1)

        size_inp_ctn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._more_options.attach_next_to(size_inp_ctn, size_lbl, Gtk.PositionType.RIGHT, 1, 1)

        size_w_lbl = Gtk.Label('W:')
        size_inp_ctn.add(size_w_lbl)
        size_w_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
        size_w_inp.get_style_context().add_class('small-pad')
        size_inp_ctn.add(size_w_inp)
        size_h_lbl = Gtk.Label('H:')
        size_inp_ctn.add(size_h_lbl)
        size_h_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
        size_h_inp.get_style_context().add_class('small-pad')
        size_inp_ctn.add(size_h_inp)

        size_err_lbl = Gtk.Label(xalign=0, width_request=190)
        size_err_lbl.get_style_context().add_class('error-text')
        self._more_options.attach_next_to(size_err_lbl, size_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

        self.widget.show_all()

        # Wiring things up

        self.bn_more_options_sensitive = AccessorBindable(setter=self._set_figure_options_sensitive)

        # Fields

        self.should_save_field = FieldView(value=GObjectPropertyBindable(self._should_save_figure_inp, 'active'))
        self.dpi_field = FieldView(value=GObjectPropertyBindable(dpi_inp, 'value'))
        self.size_w_field = FieldView(value=GObjectPropertyBindable(size_w_inp, 'value'))
        self.size_h_field = FieldView(value=GObjectPropertyBindable(size_h_inp, 'value'))

        # Error highlighting

        # Keep a reference to unnamed objects to prevent them from being garbage collected
        self.dpi_field.__my_refs = [
            add_style_class_when_flags(dpi_inp, 'error', flags=self.dpi_field.errors_out),
            GObjectPropertyBindable(dpi_err_lbl, 'label').bind_from(
                message_from_flags(field_name='Figure DPI', flags=self.dpi_field.errors_out))]

        def figure_size_err_message(w_errors: Set[ValidationFlag], h_errors: Set[ValidationFlag]) -> str:
            if len(w_errors) + len(h_errors) == 0:
                return ''

            if len(w_errors) > 0 and len(h_errors) > 0:
                message = 'Width and height'
                if ValidationFlag.CANNOT_BE_EMPTY in w_errors.intersection(h_errors):
                    message += ' cannot be empty'
                else:
                    message += ' must be greater than 0'
                return message
            else:
                if len(w_errors) > 0:
                    message = 'Width'
                    errors = w_errors
                else:
                    message = 'Height'
                    errors = h_errors

                if ValidationFlag.CANNOT_BE_EMPTY in errors:
                    message += ' cannot be empty'
                elif ValidationFlag.MUST_BE_POSITIVE in errors:
                    message += ' must be greater than 0'
                else:
                    message += ' is invalid'

                return message

        self.size_w_field.__my_refs = [
            add_style_class_when_flags(size_w_inp, 'error', flags=self.size_w_field.errors_out),
            add_style_class_when_flags(size_h_inp, 'error', flags=self.size_h_field.errors_out),
            GObjectPropertyBindable(size_err_lbl, 'label').bind_from(
                bn_apply(figure_size_err_message, self.size_w_field.errors_out, self.size_h_field.errors_out))]

        dpi_inp.connect('focus-out-event', lambda *_: self.dpi_field.on_user_finished_editing.fire())
        size_w_inp.connect('focus-out-event', lambda *_: self.size_w_field.on_user_finished_editing.fire())
        size_h_inp.connect('focus-out-event', lambda *_: self.size_h_field.on_user_finished_editing.fire())

    def _set_figure_options_sensitive(self, sensitive: bool) -> None:
        self._more_options.props.sensitive = sensitive


class FigureOptionsPresenter:
    def __init__(self, options: FigureOptions, view: FigureOptionsView) -> None:
        self._options = options
        self._view = view
        self.__destroyed = False
        self.__cleanup_tasks = []

        data_bindings = [
            self._options.bn_should_save.bind_to(self._view.should_save_field.value),
            self._options.bn_should_save.bind_to(self._view.bn_more_options_sensitive)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        self._field_presenters = [
            FieldPresenter(self._options.bn_dpi, self._options.dpi_err, self._view.dpi_field),
            FieldPresenter(self._options.bn_size_w, self._options.size_w_err, self._view.size_w_field),
            FieldPresenter(self._options.bn_size_h, self._options.size_h_err, self._view.size_h_field)]
        self.__cleanup_tasks.extend(fp.destroy for fp in self._field_presenters)

    def update_errors_visibility(self) -> None:
        for fp in self._field_presenters:
            fp.show_errors()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
