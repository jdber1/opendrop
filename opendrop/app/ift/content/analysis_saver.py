from pathlib import Path
from typing import Optional

from gi.repository import Gtk, Gdk

from opendrop.app.common.content.analysis_saver import FigureOptionsView, FigureOptionsPresenter
from opendrop.app.ift.model.analysis_saver import IFTAnalysisSaverOptions
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import AccessorBindable
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.utility.events import Event
from opendrop.utility.validation import message_from_flags, add_style_class_when_flags, FieldView, \
    FieldPresenter


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

        self.drop_residuals_figure_save_options = FigureOptionsView('drop profile fit residuals plot')
        figures_content.attach(self.drop_residuals_figure_save_options.widget, 0, 0, 1, 1)

        self.ift_figure_save_options = FigureOptionsView('interfacial tension plot')
        figures_content.attach(self.ift_figure_save_options.widget, 0, 1, 1, 1)

        self.volume_figure_save_options = FigureOptionsView('volume plot')
        figures_content.attach(self.volume_figure_save_options.widget, 0, 2, 1, 1)

        self.surface_area_figure_save_options = FigureOptionsView('surface area plot')
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
            value=AccessorBindable(self._get_save_dir_parent, self._set_save_dir_parent))
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
    def __init__(self, options: IFTAnalysisSaverOptions, view: IFTAnalysisSaverView) -> None:
        self._options = options
        self._view = view
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._drop_residuals_figure_save_options = FigureOptionsPresenter(
            options=self._options.drop_residuals_figure_opts,
            view=self._view.drop_residuals_figure_save_options)
        self.__cleanup_tasks.append(self._drop_residuals_figure_save_options.destroy)

        self._ift_figure_save_options = FigureOptionsPresenter(
            options=self._options.ift_figure_opts,
            view=self._view.ift_figure_save_options)
        self.__cleanup_tasks.append(self._ift_figure_save_options.destroy)

        self._volume_figure_save_options = FigureOptionsPresenter(
            options=self._options.volume_figure_opts,
            view=self._view.volume_figure_save_options)
        self.__cleanup_tasks.append(self._volume_figure_save_options.destroy)

        self._surface_area_figure_save_options = FigureOptionsPresenter(
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

        self._drop_residuals_figure_save_options.update_errors_visibility()
        self._ift_figure_save_options.update_errors_visibility()
        self._volume_figure_save_options.update_errors_visibility()
        self._surface_area_figure_save_options.update_errors_visibility()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
