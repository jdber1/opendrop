from pathlib import Path
from typing import Optional, Set

from gi.repository import Gtk, Gdk

from opendrop.app.ift.model.analysis_saver import IFTAnalysisSaverOptions
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import bindable_function
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.utility.events import Event
from opendrop.utility.validation import message_from_flags, add_style_class_when_flags, ValidationFlag, FieldView, \
    FieldPresenter
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry


class IFTAnalysisSaverView(GtkWidgetView[Gtk.Window]):
    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }

    .small-combobox .combo {
        min-height: 0px;
        min-width: 0px;
    }
    
    .ift-analysis-saver-view-footer-button {
        min-height: 0px;
        min-width: 60px;
        padding: 10px 4px 10px 4px;
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

    class FigureOptionsView(GtkWidgetView[Gtk.Grid]):
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

            self.bn_more_options_sensitive = AtomicBindableAdapter(setter=self._set_figure_options_sensitive)

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

            @bindable_function
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
                    figure_size_err_message(self.size_w_field.errors_out, self.size_h_field.errors_out))]

            dpi_inp.connect('focus-out-event', lambda *_: self.dpi_field.on_user_finished_editing.fire())
            size_w_inp.connect('focus-out-event', lambda *_: self.size_w_field.on_user_finished_editing.fire())
            size_h_inp.connect('focus-out-event', lambda *_: self.size_h_field.on_user_finished_editing.fire())

        def _set_figure_options_sensitive(self, sensitive: bool) -> None:
            self._more_options.props.sensitive = sensitive

    def __init__(self, transient_for: Optional[Gtk.Window] = None) -> None:
        self.widget = Gtk.Window(resizable=False, modal=True, transient_for=transient_for)

        # Add a reference to self in the widget, otherwise self gets garbage collected for some reason.
        self.widget.__ref_to_view = self

        body = Gtk.Grid(margin=10, row_spacing=10)
        self.widget.add(body)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        body.attach(content, 0, 0, 1, 1)

        save_location_frame = Gtk.Frame(label='Save location')
        content.add(save_location_frame)
        save_location_content = Gtk.Grid(margin=10, column_spacing=10, row_spacing=5)
        save_location_frame.add(save_location_content)

        save_dir_lbl = Gtk.Label('Parent:', xalign=0)
        save_location_content.attach(save_dir_lbl, 0, 0, 1, 1)

        self._save_dir_parent_inp = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER, hexpand=True)
        self._save_dir_parent_inp.get_style_context().add_class('small-combobox')
        save_location_content.attach_next_to(self._save_dir_parent_inp, save_dir_lbl, Gtk.PositionType.RIGHT, 1, 1)

        save_dir_parent_err_lbl = Gtk.Label(xalign=0, width_request=190)
        save_dir_parent_err_lbl.get_style_context().add_class('error-text')
        save_location_content.attach_next_to(save_dir_parent_err_lbl, self._save_dir_parent_inp, Gtk.PositionType.RIGHT, 1, 1)

        save_name_lbl = Gtk.Label('Name:', xalign=0)
        save_location_content.attach(save_name_lbl, 0, 1, 1, 1)

        save_dir_name_inp = Gtk.Entry()
        save_dir_name_inp.get_style_context().add_class('small-pad')
        save_location_content.attach_next_to(save_dir_name_inp, save_name_lbl, Gtk.PositionType.RIGHT, 1, 1)

        save_dir_name_err_lbl = Gtk.Label(xalign=0, width_request=190)
        save_dir_name_err_lbl.get_style_context().add_class('error-text')
        save_location_content.attach_next_to(save_dir_name_err_lbl, save_dir_name_inp, Gtk.PositionType.RIGHT, 1, 1)

        figures_frame = Gtk.Frame(label='Figures')
        content.add(figures_frame)
        figures_content = Gtk.Grid(margin=10, column_spacing=10, row_spacing=5)
        figures_frame.add(figures_content)

        self.drop_residuals_figure_save_options = self.FigureOptionsView('drop profile fit residuals plot')
        figures_content.attach(self.drop_residuals_figure_save_options.widget, 0, 0, 1, 1)

        self.ift_figure_save_options = self.FigureOptionsView('interfacial tension plot')
        figures_content.attach(self.ift_figure_save_options.widget, 0, 1, 1, 1)

        self.volume_figure_save_options = self.FigureOptionsView('volume plot')
        figures_content.attach(self.volume_figure_save_options.widget, 0, 2, 1, 1)

        self.surface_area_figure_save_options = self.FigureOptionsView('surface area plot')
        figures_content.attach(self.surface_area_figure_save_options.widget, 0, 3, 1, 1)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        body.attach_next_to(footer, content, Gtk.PositionType.BOTTOM, 1, 1)

        ok_btn = Gtk.Button('OK')
        ok_btn.get_style_context().add_class('ift-analysis-saver-view-footer-button')
        footer.pack_end(ok_btn, expand=False, fill=False, padding=0)

        cancel_btn = Gtk.Button('Cancel')
        cancel_btn.get_style_context().add_class('ift-analysis-saver-view-footer-button')
        footer.pack_end(cancel_btn, expand=False, fill=False, padding=0)

        self.widget.show_all()

        # Wiring things up

        self.on_ok_btn_clicked = Event()
        self.on_cancel_btn_clicked = Event()

        ok_btn.connect('clicked', lambda *_: self.on_ok_btn_clicked.fire())
        cancel_btn.connect('clicked', lambda *_: self.on_cancel_btn_clicked.fire())
        self.widget.connect('delete-event', self._hdl_widget_delete_event)

        self.save_dir_parent_field = FieldView(
            value=AtomicBindableAdapter(self._get_save_dir_parent, self._set_save_dir_parent))
        self.save_dir_name_field = FieldView(
            value=GObjectPropertyBindable(save_dir_name_inp, 'text'))

        # Error highlighting

        # Keep a reference to unnamed objects to prevent them from being garbage collected
        self.save_dir_parent_field.__my_refs = [
            add_style_class_when_flags(self._save_dir_parent_inp, 'error', flags=self.save_dir_parent_field.errors_out),
            GObjectPropertyBindable(save_dir_parent_err_lbl, 'label').bind_from(
                message_from_flags(field_name='Parent', flags=self.save_dir_parent_field.errors_out))]

        self.save_dir_name_field.__my_refs = [
            add_style_class_when_flags(save_dir_name_inp, 'error', flags=self.save_dir_name_field.errors_out),
            GObjectPropertyBindable(save_dir_name_err_lbl, 'label').bind_from(
                message_from_flags(field_name='Name', flags=self.save_dir_name_field.errors_out))]

        save_dir_name_inp.connect('focus-out-event', lambda *_: self.save_dir_name_field.on_user_finished_editing.fire())

    def _hdl_widget_delete_event(self, widget: Gtk.Dialog, event: Gdk.Event) -> bool:
        self.on_cancel_btn_clicked.fire()
        # return True to block the dialog from closing.
        return True

    def _get_save_dir_parent(self) -> Path:
        path_str = self._save_dir_parent_inp.get_filename()
        path = Path(path_str) if path_str is not None else None
        return path

    def _set_save_dir_parent(self, path: Optional[Path]) -> None:
        if path is None:
            self._save_dir_parent_inp.unselect_all()
            return

        path = str(path)
        self._save_dir_parent_inp.set_filename(path)

    def flush(self) -> None:
        self.save_dir_parent_field.value.poke()

    def destroy(self) -> None:
        self.widget.destroy()


class IFTAnalysisSaverPresenter:
    class FigureOptionsPresenter:
        def __init__(self, options: IFTAnalysisSaverOptions.FigureOptions,
                     view: IFTAnalysisSaverView.FigureOptionsView) -> None:
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

        def show_errors(self) -> None:
            for fp in self._field_presenters:
                fp.show_errors()

        def destroy(self) -> None:
            assert not self.__destroyed
            for f in self.__cleanup_tasks:
                f()
            self.__destroyed = True

    def __init__(self, options: IFTAnalysisSaverOptions, view: IFTAnalysisSaverView) -> None:
        self._options = options
        self._view = view
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._drop_residuals_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.drop_residuals_figure_opts,
            view=self._view.drop_residuals_figure_save_options)
        self.__cleanup_tasks.append(self._drop_residuals_figure_save_options.destroy)

        self._ift_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.ift_figure_opts,
            view=self._view.ift_figure_save_options)
        self.__cleanup_tasks.append(self._ift_figure_save_options.destroy)

        self._volume_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.volume_figure_opts,
            view=self._view.volume_figure_save_options)
        self.__cleanup_tasks.append(self._volume_figure_save_options.destroy)

        self._surface_area_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.surface_area_figure_opts,
            view=self._view.surface_area_figure_save_options)
        self.__cleanup_tasks.append(self._surface_area_figure_save_options.destroy)

        self._field_presenters = [
            FieldPresenter(value=self._options.bn_save_dir_parent,
                           errors=self._options.save_dir_parent_err,
                           field_view=self._view.save_dir_parent_field),
            FieldPresenter(value=self._options.bn_save_dir_name,
                           errors=self._options.save_dir_name_err,
                           field_view=self._view.save_dir_name_field)]
        self.__cleanup_tasks.extend(fp.destroy for fp in self._field_presenters)

        event_connections = [
            self._view.on_ok_btn_clicked.connect(self._ok),
            self._view.on_cancel_btn_clicked.connect(self._cancel)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self.on_user_finished_editing = Event()

    def _ok(self) -> None:
        self._view.flush()

        if self._options.has_errors:
            self._show_errors()
            return

        self.on_user_finished_editing.fire(True)

    def _cancel(self) -> None:
        self.on_user_finished_editing.fire(False)

    def _show_errors(self) -> None:
        for fp in self._field_presenters:
            fp.show_errors()

        self._drop_residuals_figure_save_options.show_errors()
        self._ift_figure_save_options.show_errors()
        self._volume_figure_save_options.show_errors()
        self._surface_area_figure_save_options.show_errors()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
