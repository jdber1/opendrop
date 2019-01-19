from pathlib import Path
from typing import Optional, Set

from gi.repository import Gtk, Gdk

from opendrop.app.ift.model.analysis_saver import IFTAnalysisSaverOptions
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import BuiltinSetBindable, bindable_function, if_expr
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.utility.validation import message_from_flags, associate_style_class_to_widget_when_flags_present, \
    ValidationFlag
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
        class ErrorsView:
            def __init__(self, view: 'IFTAnalysisSaverView.FigureOptionsView') -> None:
                self._view = view

                self.bn_figure_dpi_err_msg = AtomicBindableAdapter(
                    setter=self._set_figure_dpi_err_msg)  # type: AtomicBindable[Optional[str]]
                self.bn_figure_size_err_msg = AtomicBindableAdapter(
                    setter=self._set_figure_size_err_msg)  # type: AtomicBindable[Optional[str]]

                self.bn_figure_dpi_touched = AtomicBindableVar(False)
                self.bn_figure_size_touched = AtomicBindableVar(False)

                self._view._dpi_inp.connect(
                    'focus-out-event', lambda *_: self.bn_figure_dpi_touched.set(True))
                self._view._size_w_inp.connect(
                    'focus-out-event', lambda *_: self.bn_figure_size_touched.set(True))
                self._view._size_h_inp.connect(
                    'focus-out-event', lambda *_: self.bn_figure_size_touched.set(True))

            def reset_touches(self) -> None:
                self.bn_figure_dpi_touched.set(False)
                self.bn_figure_size_touched.set(False)

            def touch_all(self) -> None:
                self.bn_figure_dpi_touched.set(True)
                self.bn_figure_size_touched.set(True)

            def _set_figure_dpi_err_msg(self, err_msg: Optional[str]) -> None:
                self._view._figure_dpi_err_msg_lbl.props.label = err_msg

                if err_msg is not None:
                    self._view._dpi_inp.get_style_context().add_class('error')
                else:
                    self._view._dpi_inp.get_style_context().remove_class('error')

            def _set_figure_size_err_msg(self, err_msg: Optional[str]) -> None:
                self._view._figure_size_err_msg_lbl.props.label = err_msg

                if err_msg is not None:
                    self._view._size_w_inp.get_style_context().add_class('error')
                    self._view._size_h_inp.get_style_context().add_class('error')
                else:
                    self._view._size_w_inp.get_style_context().remove_class('error')
                    self._view._size_h_inp.get_style_context().remove_class('error')

        def __init__(self, figure_name: str) -> None:
            self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

            self._should_save_figure_inp = Gtk.CheckButton(label='Save {}'.format(figure_name))
            self.widget.add(self._should_save_figure_inp)

            more_options = Gtk.Grid(margin_left=30, row_spacing=5, column_spacing=10)
            self.widget.add(more_options)

            dpi_lbl = Gtk.Label('Figure DPI:', xalign=0)
            more_options.attach(dpi_lbl, 0, 0, 1, 1)

            dpi_inp_ctn = Gtk.Grid()
            more_options.attach_next_to(dpi_inp_ctn, dpi_lbl, Gtk.PositionType.RIGHT, 1, 1)
            self._dpi_inp = IntegerEntry(value=300, lower=72, upper=10000, width_chars=5)
            self._dpi_inp.get_style_context().add_class('small-pad')
            dpi_inp_ctn.add(self._dpi_inp)

            dpi_err_lbl = Gtk.Label(xalign=0, width_request=190)
            dpi_err_lbl.get_style_context().add_class('error-text')
            more_options.attach_next_to(dpi_err_lbl, dpi_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

            size_lbl = Gtk.Label('Figure size (cm):', xalign=0)
            more_options.attach(size_lbl, 0, 1, 1, 1)

            size_inp_ctn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            more_options.attach_next_to(size_inp_ctn, size_lbl, Gtk.PositionType.RIGHT, 1, 1)

            size_w_lbl = Gtk.Label('W:')
            size_inp_ctn.add(size_w_lbl)
            self._size_w_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
            self._size_w_inp.get_style_context().add_class('small-pad')
            size_inp_ctn.add(self._size_w_inp)
            size_h_lbl = Gtk.Label('H:')
            size_inp_ctn.add(size_h_lbl)
            self._size_h_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
            self._size_h_inp.get_style_context().add_class('small-pad')
            size_inp_ctn.add(self._size_h_inp)

            size_err_lbl = Gtk.Label(xalign=0, width_request=190)
            size_err_lbl.get_style_context().add_class('error-text')
            more_options.attach_next_to(size_err_lbl, size_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

            self.widget.show_all()

            # Wiring things up

            self.bn_more_options_sensitive = AtomicBindableAdapter(setter=self._set_figure_options_sensitive)
            self.bn_should_save = GObjectPropertyBindable(self._should_save_figure_inp, 'active')  # type: AtomicBindable[bool]
            self.bn_dpi = GObjectPropertyBindable(self._dpi_inp, 'value')  # type: AtomicBindable[int]
            self.bn_size_w = GObjectPropertyBindable(self._size_w_inp, 'value')  # type: AtomicBindable[int]
            self.bn_size_h = GObjectPropertyBindable(self._size_h_inp, 'value')  # type: AtomicBindable[int]

            # Error highlighting

            self.dpi_err = BuiltinSetBindable()
            self.size_w_err = BuiltinSetBindable()
            self.size_h_err = BuiltinSetBindable()

            self.figure_dpi_touched = AtomicBindableVar(False)
            self.figure_size_w_touched = AtomicBindableVar(False)
            self.figure_size_h_touched = AtomicBindableVar(False)

            # Keep a reference to unnamed objects to prevent them from being garbage collected
            self._refs = []

            self._refs.extend([
                associate_style_class_to_widget_when_flags_present(self._dpi_inp, 'error', flags=self.dpi_err),
                GObjectPropertyBindable(dpi_err_lbl, 'label').bind_from(
                    message_from_flags(field_name='Figure DPI', flags=self.dpi_err))]),

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

            self._refs.extend([
                associate_style_class_to_widget_when_flags_present(self._size_w_inp, 'error', flags=self.size_w_err),
                associate_style_class_to_widget_when_flags_present(self._size_h_inp, 'error', flags=self.size_h_err),
                GObjectPropertyBindable(size_err_lbl, 'label').bind_from(
                    src=figure_size_err_message(self.size_w_err, self.size_h_err))])

            self._dpi_inp.connect('focus-out-event', lambda *_: self.figure_dpi_touched.set(True))
            self._size_w_inp.connect('focus-out-event', lambda *_: self.figure_size_w_touched.set(True))
            self._size_h_inp.connect('focus-out-event', lambda *_: self.figure_size_h_touched.set(True))

        def _set_figure_options_sensitive(self, sensitive: bool) -> None:
            self._dpi_inp.props.sensitive = sensitive
            self._size_w_inp.props.sensitive = sensitive
            self._size_h_inp.props.sensitive = sensitive

        def touch_all(self):
            self.figure_dpi_touched.set(True)
            self.figure_size_w_touched.set(True)
            self.figure_size_h_touched.set(True)

        def reset_touches(self):
            self.figure_dpi_touched.set(False)
            self.figure_size_w_touched.set(False)
            self.figure_size_h_touched.set(False)

    def __init__(self, transient_for: Optional[Gtk.Window] = None) -> None:
        self.widget = Gtk.Window(resizable=False, modal=True, transient_for=transient_for)

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

        self.bn_save_dir_parent = AtomicBindableAdapter(self._get_save_dir_parent, self._set_save_dir_parent)
        self.bn_save_dir_name = GObjectPropertyBindable(save_dir_name_inp, 'text')

        # Error highlighting

        self.save_dir_parent_err = BuiltinSetBindable()
        self.save_dir_name_err = BuiltinSetBindable()
        self.save_dir_parent_touched = AtomicBindableVar(False)
        self.save_dir_name_touched = AtomicBindableVar(False)

        # Keep a reference to unnamed objects to prevent them from being garbage collected
        self._refs = (
            associate_style_class_to_widget_when_flags_present(self._save_dir_parent_inp, 'error', flags=self.save_dir_parent_err),
            GObjectPropertyBindable(save_dir_parent_err_lbl, 'label').bind_from(
                message_from_flags(field_name='Parent', flags=self.save_dir_parent_err)),

            associate_style_class_to_widget_when_flags_present(save_dir_name_inp, 'error', flags=self.save_dir_name_err),
            GObjectPropertyBindable(save_dir_name_err_lbl, 'label').bind_from(
                src=message_from_flags(field_name='Name', flags=self.save_dir_name_err)))

        save_dir_name_inp.connect('focus-out-event', lambda *_: self.save_dir_name_touched.set(True))

    def _get_save_dir_parent(self) -> Path:
        return Path(self._save_dir_parent_inp.get_filename())

    def _set_save_dir_parent(self, path: Path) -> None:
        self._save_dir_parent_inp.set_filename(str(path))

    def touch_all(self) -> None:
        self.save_dir_parent_touched.set(True)
        self.save_dir_name_touched.set(True)

        self.drop_residuals_figure_save_options.touch_all()
        self.ift_figure_save_options.touch_all()
        self.volume_figure_save_options.touch_all()
        self.surface_area_figure_save_options.touch_all()

    def reset_touches(self) -> None:
        self.save_dir_parent_touched.set(False)
        self.save_dir_name_touched.set(False)

        self.drop_residuals_figure_save_options.reset_touches()
        self.ift_figure_save_options.reset_touches()
        self.volume_figure_save_options.reset_touches()
        self.surface_area_figure_save_options.reset_touches()


class IFTAnalysisSaverPresenter:
    class FigureOptionsPresenter:
        def __init__(self, options: IFTAnalysisSaverOptions.FigureOptions,
                     view: IFTAnalysisSaverView.FigureOptionsView) -> None:
            self._options = options
            self._view = view
            self.__destroyed = False
            self.__cleanup_tasks = []

            empty_err = BuiltinSetBindable()
            dpi_err = if_expr(cond=self._view.figure_dpi_touched, true=options.dpi_err, false=empty_err)
            size_w_err = if_expr(cond=self._view.figure_size_w_touched, true=options.size_w_err, false=empty_err)
            size_h_err = if_expr(cond=self._view.figure_size_h_touched, true=options.size_h_err, false=empty_err)

            data_bindings = [
                options.bn_should_save.bind_to(self._view.bn_should_save),
                options.bn_should_save.bind_to(self._view.bn_more_options_sensitive),
                options.bn_dpi.bind_to(self._view.bn_dpi),
                options.bn_size_w.bind_to(self._view.bn_size_w),
                options.bn_size_h.bind_to(self._view.bn_size_h),

                dpi_err.bind_to(self._view.dpi_err),
                size_w_err.bind_to(self._view.size_w_err),
                size_h_err.bind_to(self._view.size_h_err)]
            self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

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

        self._view.reset_touches()

        drop_residuals_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.drop_residuals_figure_opts,
            view=self._view.drop_residuals_figure_save_options)
        self.__cleanup_tasks.append(drop_residuals_figure_save_options.destroy)

        ift_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.ift_figure_opts,
            view=self._view.ift_figure_save_options)
        self.__cleanup_tasks.append(ift_figure_save_options.destroy)

        volume_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.volume_figure_opts,
            view=self._view.volume_figure_save_options)
        self.__cleanup_tasks.append(volume_figure_save_options.destroy)

        surface_area_figure_save_options = self.FigureOptionsPresenter(
            options=self._options.surface_area_figure_opts,
            view=self._view.surface_area_figure_save_options)
        self.__cleanup_tasks.append(surface_area_figure_save_options.destroy)

        empty_err = BuiltinSetBindable()
        save_dir_parent_err = if_expr(cond=self._view.save_dir_parent_touched,
                                      true=self._options.save_dir_parent_err,
                                      false=empty_err)
        save_dir_name_err = if_expr(cond=self._view.save_dir_name_touched,
                                    true=self._options.save_dir_name_err,
                                    false=empty_err)

        data_bindings = [
            Binding(self._options.bn_save_dir_parent, self._view.bn_save_dir_parent),
            Binding(self._options.bn_save_dir_name, self._view.bn_save_dir_name),

            Binding(save_dir_parent_err, self._view.save_dir_parent_err),
            Binding(save_dir_name_err, self._view.save_dir_name_err),
        ]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
