import functools
import math
from typing import MutableSequence, Optional, Sequence, MutableMapping, Callable

import cv2
import numpy as np
from gi.repository import Gtk, Pango, Gdk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.image import AxesImage

from opendrop.app.ift.model.analyser import IFTDropAnalysis
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.mytypes import Image
from opendrop.utility.bindable import Bindable, BoxBindable, AccessorBindable


class DetailView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .notebook-small-tabs tab {
         min-height: 0px;
         padding: 8px 0px;
    }
    
    .individual-detail-view-stack-switcher > * {
         min-width: 60px;
         min-height: 0px;
         padding: 6px 4px 6px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class ParametersView(GtkWidgetView[Gtk.Grid]):
        def __init__(self) -> None:
            self.widget = Gtk.Grid(row_spacing=10)

            parameters_lbl = Gtk.Label(xalign=0)
            parameters_lbl.set_markup('<b>Parameters</b>')
            self.widget.attach(parameters_lbl, 0, 0, 1, 1)

            sheet = Gtk.Grid(row_spacing=10, column_spacing=10)
            self.widget.attach(sheet, 0, 1, 1, 1)

            interfacial_tension_lbl = Gtk.Label('IFT (mN/m):', xalign=0)
            sheet.attach(interfacial_tension_lbl, 0, 0, 1, 1)

            volume_lbl = Gtk.Label('Volume (mm²):', xalign=0)
            sheet.attach(volume_lbl, 0, 1, 1, 1)

            surface_area_lbl = Gtk.Label('Surface area (mm³):', xalign=0)
            sheet.attach(surface_area_lbl, 0, 2, 1, 1)

            sheet.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1)

            worthington_lbl = Gtk.Label('Worthington:', xalign=0)
            sheet.attach(worthington_lbl, 0, 4, 1, 1)

            bond_number_lbl = Gtk.Label('Bond number:', xalign=0)
            sheet.attach(bond_number_lbl, 0, 5, 1, 1)

            apex_coords_lbl = Gtk.Label('Apex coordinates (px):', xalign=0)
            sheet.attach(apex_coords_lbl, 0, 6, 1, 1)

            image_angle_lbl = Gtk.Label('Image angle:', xalign=0)
            sheet.attach(image_angle_lbl, 0, 7, 1, 1)

            interfacial_tension_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(interfacial_tension_val, interfacial_tension_lbl, Gtk.PositionType.RIGHT, 1, 1)

            volume_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(volume_val, volume_lbl, Gtk.PositionType.RIGHT, 1, 1)

            surface_area_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(surface_area_val, surface_area_lbl, Gtk.PositionType.RIGHT, 1, 1)

            worthington_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(worthington_val, worthington_lbl, Gtk.PositionType.RIGHT, 1, 1)

            bond_number_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(bond_number_val, bond_number_lbl, Gtk.PositionType.RIGHT, 1, 1)

            apex_coords_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(apex_coords_val, apex_coords_lbl, Gtk.PositionType.RIGHT, 1, 1)

            image_angle_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(image_angle_val, image_angle_lbl, Gtk.PositionType.RIGHT, 1, 1)

            self.widget.show_all()

            # Wiring things up

            self.bn_interfacial_tension = AccessorBindable(
                setter=lambda v: interfacial_tension_val.set_text('{:.4g}'.format(v*1e3)))
            self.bn_volume = AccessorBindable(
                setter=lambda v: volume_val.set_text('{:.4g}'.format(v*1e9)))
            self.bn_surface_area = AccessorBindable(
                setter=lambda v: surface_area_val.set_text('{:.4g}'.format(v*1e6)))
            self.bn_worthington = AccessorBindable(
                setter=lambda v: worthington_val.set_text('{:.4g}'.format(v)))
            self.bn_bond_number = AccessorBindable(
                setter=lambda v: bond_number_val.set_text('{:.4g}'.format(v)))
            self.bn_apex_coords = AccessorBindable(
                setter=lambda v: apex_coords_val.set_text('({0[0]:.4g}, {0[1]:.4g})'.format(v)))
            self.bn_image_angle = AccessorBindable(
                setter=lambda v: image_angle_val.set_text('{:.4g}°'.format(math.degrees(v))))

    class DropContourFitResidualsView(GtkWidgetView[Gtk.Grid]):
        def __init__(self) -> None:
            self.widget = Gtk.Grid()

            residuals_figure = Figure(tight_layout=True)
            self._residuals_fig_canvas = FigureCanvas(residuals_figure)
            self._residuals_fig_canvas.props.hexpand = True
            self._residuals_fig_canvas.props.vexpand = True
            self.widget.add(self._residuals_fig_canvas)

            self.widget.show_all()

            # Axes
            self._residuals_figure_axes = residuals_figure.add_subplot(1, 1, 1)
            for item in (self._residuals_figure_axes.get_xticklabels() + self._residuals_figure_axes.get_yticklabels()):
                item.set_fontsize(8)

            # Wiring things up
            self.bn_residuals = AccessorBindable(setter=self._set_residuals)

        def _set_residuals(self, residuals: np.ndarray) -> None:
            axes = self._residuals_figure_axes
            axes.clear()

            if residuals.size == 0:
                axes.set_axis_off()
                self._residuals_fig_canvas.queue_draw()
                return

            axes.set_axis_on()
            axes.plot(residuals[:, 0], residuals[:, 1], color='#0080ff', marker='o', linestyle='')
            self._residuals_fig_canvas.queue_draw()

    class DropContourView(GtkWidgetView[Gtk.Grid]):
        def __init__(self) -> None:
            self.widget = Gtk.Grid()

            drop_fig = Figure(tight_layout=True)
            self._drop_fig_canvas = FigureCanvas(drop_fig)
            self._drop_fig_canvas.props.hexpand = True
            self._drop_fig_canvas.props.vexpand = True
            self.widget.add(self._drop_fig_canvas)

            self.widget.show_all()

            # Axes
            self._drop_fig_ax = drop_fig.add_subplot(1, 1, 1)
            self._drop_fig_ax.set_aspect('equal', 'box')
            self._drop_fig_ax.xaxis.tick_top()
            for item in (self._drop_fig_ax.get_xticklabels() + self._drop_fig_ax.get_yticklabels()):
                item.set_fontsize(8)

            self._drop_aximg = AxesImage(ax=self._drop_fig_ax)
            # Place holder transparent 1x1 image (rgba format)
            self._drop_aximg.set_data(np.zeros((1, 1, 4)))
            self._drop_fig_ax.add_image(self._drop_aximg)
            self._drop_contour_line = self._drop_fig_ax.plot([], linestyle='-', color='#0080ff', linewidth=1.5)[0]
            self._drop_contour_fit_line = self._drop_fig_ax.plot([], linestyle='-', color='#ff0080', linewidth=1)[0]

            # Wiring things up
            self.bn_drop_image = AccessorBindable(setter=self._set_drop_image)
            self.bn_drop_contour = AccessorBindable(setter=self._set_drop_contour)
            self.bn_drop_contour_fit = AccessorBindable(setter=self._set_drop_contour_fit)

        def _set_drop_image(self, image: Optional[Image]) -> None:
            if image is None:
                self._drop_fig_ax.set_axis_off()
                self._drop_aximg.set_data(np.zeros((1, 1, 4)))
                return

            self._drop_fig_ax.set_axis_on()

            # Use a scaled down image so it draws faster.
            thumb_size = (min(400, image.shape[1]), min(400, image.shape[0]))
            image_thumb = cv2.resize(image, dsize=thumb_size)
            self._drop_aximg.set_data(image_thumb)

            self._drop_aximg.set_extent((0, image.shape[1], image.shape[0], 0))
            self._drop_fig_canvas.queue_draw()

        def _set_drop_contour(self, contour: np.ndarray) -> None:
            self._drop_contour_line.set_data(contour.T)
            self._drop_fig_canvas.queue_draw()

        def _set_drop_contour_fit(self, contour: np.ndarray) -> None:
            self._drop_contour_fit_line.set_data(contour.T)
            self._drop_fig_canvas.queue_draw()

    class LogView(GtkWidgetView[Gtk.ScrolledWindow]):
        def __init__(self) -> None:
            self.widget = Gtk.ScrolledWindow()
            log_text_view = Gtk.TextView(monospace=True, editable=False, wrap_mode=Gtk.WrapMode.CHAR, hexpand=True,
                                         vexpand=True, margin=10)
            self.widget.add(log_text_view)
            self.widget.show_all()

            # Wiring things up

            self.bn_log_text = AccessorBindable(setter=lambda v: log_text_view.get_buffer().set_text(v))

    def __init__(self) -> None:
        self.widget = Gtk.Stack(margin=10)

        self._data_grid = Gtk.Grid(column_spacing=10)
        self.widget.add(self._data_grid)

        self.parameters = self.ParametersView()
        self._data_grid.attach(self.parameters.widget, 0, 0, 1, 1)

        notebook_for_drop_resids_and_log = Gtk.Notebook(hexpand=True, vexpand=True)
        notebook_for_drop_resids_and_log.get_style_context().add_class('notebook-small-tabs')
        self._data_grid.attach(notebook_for_drop_resids_and_log, 1, 0, 1, 1)

        self.drop_contour = self.DropContourView()
        notebook_for_drop_resids_and_log.append_page(self.drop_contour.widget, Gtk.Label('Drop contour'))

        self.drop_contour_fit_residuals = self.DropContourFitResidualsView()
        notebook_for_drop_resids_and_log.append_page(self.drop_contour_fit_residuals.widget, Gtk.Label('Fit residuals'))

        self.log = self.LogView()
        notebook_for_drop_resids_and_log.append_page(self.log.widget, Gtk.Label('Log'))
        self._data_grid.show_all()

        self._waiting_for_data_placeholder_lbl = Gtk.Label()
        self._waiting_for_data_placeholder_lbl.set_markup('<b>Waiting for data...</b>')
        self._waiting_for_data_placeholder_lbl.show_all()
        self.widget.add(self._waiting_for_data_placeholder_lbl)

        self.widget.show_all()

        self._is_waiting_for_data = False
        self.widget.set_visible_child(self._waiting_for_data_placeholder_lbl)

    @property
    def is_waiting_for_data(self) -> bool:
        return self._is_waiting_for_data

    @is_waiting_for_data.setter
    def is_waiting_for_data(self, is_waiting: bool) -> None:
        if self.is_waiting_for_data is is_waiting:
            return

        if is_waiting:
            self.widget.set_visible_child(self._waiting_for_data_placeholder_lbl)
        else:
            self.widget.set_visible_child(self._data_grid)

        self._is_waiting_for_data = is_waiting


class MasterView(GtkWidgetView[Gtk.Grid]):
    class Row:
        STATUS_COL = 1
        LOG_COL = 2

        def __init__(self, model: Gtk.ListStore, row_ref: Gtk.TreeRowReference) -> None:
            self._model = model
            self._row_ref = row_ref

            self.bn_selected = BoxBindable(False)

        status_text = property()

        @status_text.setter
        def status_text(self, text: str) -> None:
            self._model.set_value(self._get_tree_iter(), column=self.STATUS_COL, value=text)

        log_text = property()

        @log_text.setter
        def log_text(self, text: str) -> None:
            self._model.set_value(self._get_tree_iter(), column=self.LOG_COL, value=text)

        def _get_tree_iter(self) -> Gtk.TreeIter:
            return self._model.get_iter(self._row_ref.get_path())

    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        self._rows = []  # type: MutableSequence[MasterView.Row]
        self._rows_cleanup_tasks = []  # type: MutableSequence[Callable]

        overview_lbl = Gtk.Label(xalign=0, margin=5)
        overview_lbl.set_markup('<b>Overview</b>')
        self.widget.attach(overview_lbl, 0, 0, 1, 1)

        self.fits = Gtk.ListStore(int, str, str)

        fits_view_sw = Gtk.ScrolledWindow(height_request=100, hexpand=True)
        self.widget.attach(fits_view_sw, 0, 1, 1, 1)

        fits_view = Gtk.TreeView(model=self.fits, enable_search=False, enable_grid_lines=Gtk.TreeViewGridLines.BOTH,
                                 vexpand=True)
        fits_view_sw.add(fits_view)

        self.fits_view = fits_view

        frame_num_col = Gtk.TreeViewColumn('Frame', Gtk.CellRendererText(), text=0)
        fits_view.append_column(frame_num_col)

        status_col = Gtk.TreeViewColumn('Status', Gtk.CellRendererText(), text=1)
        fits_view.append_column(status_col)

        log_col = Gtk.TreeViewColumn('Log', Gtk.CellRendererText(font='Monospace', ellipsize=Pango.EllipsizeMode.END),
                                     text=2)
        fits_view.append_column(log_col)

        self.widget.show_all()

        # Wiring things up

        self._fits_selection = fits_view.get_selection()
        self._hdl_fits_view_selection_changed_id = self._fits_selection.connect(
            'changed', self._hdl_fits_view_selection_changed)

    @property
    def visible(self) -> bool:
        return self.widget.props.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self.widget.props.visible = value

    def clear(self) -> None:
        self._rows = []
        for f in self._rows_cleanup_tasks:
            f()
        self._rows_cleanup_tasks = []
        self.fits.clear()

    def new_row(self) -> 'MasterView.Row':
        num_rows = self.fits.iter_n_children()
        frame_num = num_rows + 1

        tree_iter = self.fits.append((frame_num, None, None))
        row_ref = Gtk.TreeRowReference(model=self.fits, path=self.fits.get_path(tree_iter))

        row = self.Row(self.fits, row_ref)
        ec = row.bn_selected.on_changed.connect(functools.partial(self._hdl_row_selected_changed, row), weak_ref=False)
        self._rows_cleanup_tasks.append(ec.disconnect)
        self._rows.append(row)

        if len(self._rows) == 1:
            row.bn_selected.set(True)

        return row

    def _get_row_from_tree_iter(self, tree_iter: Gtk.TreeIter) -> 'MasterView.Row':
        row_ref = Gtk.TreeRowReference(model=self.fits, path=self.fits.get_path(tree_iter))
        for row in self._rows:
            if row._row_ref.get_path() == row_ref.get_path():
                return row
        else:
            raise ValueError('No row found.')

    def _deselect_other_rows(self, except_this_row: 'MasterView.Row') -> None:
        for row in self._rows:
            if row.bn_selected.get() and row is not except_this_row:
                row.bn_selected.set(False)

    def _hdl_fits_view_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        _, tree_iter = selection.get_selected()

        if tree_iter is None:
            # No selection, set `bn_selected` to False for all rows.
            for row in self._rows:
                if row.bn_selected.get():
                    row.bn_selected.set(False)
            return

        try:
            row = self._get_row_from_tree_iter(tree_iter)
        except ValueError:
            # Row no longer exists, perhaps this callback was called late.
            return

        selection.handler_block(self._hdl_fits_view_selection_changed_id)
        row.bn_selected.set(True)
        self._deselect_other_rows(row)
        selection.handler_unblock(self._hdl_fits_view_selection_changed_id)

    def _hdl_row_selected_changed(self, row: 'MasterView.Row') -> None:
        if row.bn_selected.get():
            self._deselect_other_rows(row)
            self._fits_selection.select_path(row._row_ref.get_path())
        elif all([not r.bn_selected.get() for r in self._rows]):
            # If no rows are selected, select the first row.
            self._rows[0].bn_selected.set(True)


class IndividualFitView(GtkWidgetView[Gtk.Paned]):
    def __init__(self) -> None:
        self.widget = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)

        self.detail = DetailView()
        self.widget.pack1(self.detail.widget, resize=True, shrink=False)

        self.master = MasterView()
        self.widget.pack2(self.master.widget, resize=False, shrink=False)

        self.widget.show_all()


class DetailPresenter:
    def __init__(self, drop: IFTDropAnalysis, view: DetailView) -> None:
        self._drop = drop
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        params_view = self._view.parameters
        log_view = self._view.log

        data_bindings = [
            self._drop.bn_interfacial_tension.bind_to(params_view.bn_interfacial_tension),
            self._drop.bn_volume.bind_to(params_view.bn_volume),
            self._drop.bn_surface_area.bind_to(params_view.bn_surface_area),
            self._drop.bn_worthington.bind_to(params_view.bn_worthington),
            self._drop.bn_bond_number.bind_to(params_view.bn_bond_number),
            self._drop.bn_apex_coords_px.bind_to(params_view.bn_apex_coords),
            self._drop.bn_apex_rot.bind_to(params_view.bn_image_angle),
            self._drop.bn_log.bind_to(log_view.bn_log_text)]
        self.__cleanup_tasks.extend([db.unbind for db in data_bindings])

        event_connections = [
            self._drop.bn_status.on_changed.connect(self._hdl_drop_status_changed),
            self._drop.bn_image_annotations.on_changed.connect(self._hdl_image_annotations_changed),
            self._drop.on_drop_contour_fit_changed.connect(self._update_view_drop_contour_fit_and_residuals)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        self._hdl_drop_status_changed()
        self._hdl_image_annotations_changed()
        self._update_view_drop_contour_fit_and_residuals()

    def _hdl_drop_status_changed(self) -> None:
        status = self._drop.status
        self._view.is_waiting_for_data = (status is IFTDropAnalysis.Status.WAITING_FOR_IMAGE or
                                          status is IFTDropAnalysis.Status.READY_TO_FIT)

    def _hdl_image_annotations_changed(self) -> None:
        image_annotations = self._drop.image_annotations

        if image_annotations is None:
            drop_image = None
            drop_contour_px = np.empty((0, 2))
        else:
            drop_region_px = image_annotations.drop_region_px

            image = self._drop.image
            drop_image = image[drop_region_px.y0:drop_region_px.y1, drop_region_px.x0:drop_region_px.x1]

            drop_contour_px = image_annotations.drop_contour_px.copy()
            drop_contour_px -= drop_region_px.pos

        self._view.drop_contour.bn_drop_image.set(drop_image)
        self._view.drop_contour.bn_drop_contour.set(drop_contour_px)

    def _update_view_drop_contour_fit_and_residuals(self) -> None:
        drop_contour_fit = self._drop.generate_drop_contour_fit(samples=50)
        residuals = self._drop.drop_contour_fit_residuals

        if drop_contour_fit is None or residuals is None:
            drop_contour_fit = np.empty((0, 2))
            residuals = np.empty((0, 2))
        else:
            drop_contour_fit += self._drop.apex_coords_px
            drop_contour_fit -= self._drop.image_annotations.drop_region_px.pos

        self._view.drop_contour.bn_drop_contour_fit.set(drop_contour_fit)
        self._view.drop_contour_fit_residuals.bn_residuals.set(residuals)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class MasterPresenter:
    def __init__(self, drops: Sequence[IFTDropAnalysis], view: MasterView) -> None:
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._drop_to_row = {}  # type: MutableMapping[IFTDropAnalysis, MasterView.Row]
        self.bn_selected = BoxBindable(None)  # type: Bindable[Optional[IFTDropAnalysis]]

        self._view.clear()
        self.add_drops(drops)

        # Only show an overview if more than one drop analysis.
        self._view.visible = len(drops) > 1

    def add_drops(self, drops: Sequence[IFTDropAnalysis]) -> None:
        for drop in drops:
            self.add_drop(drop)

    def add_drop(self, drop: IFTDropAnalysis) -> None:
        row = self._view.new_row()
        self._drop_to_row[drop] = row

        event_connections = [
            drop.bn_status.on_changed.connect(functools.partial(self._update_row_status_text, row, drop),
                                              weak_ref=False),
            drop.bn_log.on_changed.connect(functools.partial(self._update_row_log_text, row, drop), weak_ref=False),
            row.bn_selected.on_changed.connect(functools.partial(self._hdl_row_selected_changed, row), weak_ref=False)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        self._update_row_status_text(row, drop)
        self._update_row_log_text(row, drop)
        self._hdl_row_selected_changed(row)

    def _update_row_status_text(self, row: MasterView.Row, drop: IFTDropAnalysis) -> None:
        row.status_text = str(drop.status)

    def _update_row_log_text(self, row: MasterView.Row, drop: IFTDropAnalysis) -> None:
        log = drop.log

        if log == '':
            log_last_line = ''
        else:
            log_last_line = log.splitlines()[-1]

        row.log_text = log_last_line

    def _hdl_row_selected_changed(self, row: MasterView.Row) -> None:
        if not row.bn_selected.get():
            return

        drop = self._drop_from_row(row)
        self.bn_selected.set(drop)

    def _drop_from_row(self, row: MasterView.Row) -> IFTDropAnalysis:
        for candidate_drop, candidate_row in self._drop_to_row.items():
            if candidate_row is row:
                return candidate_drop
        else:
            raise ValueError('Could not find drop.')

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class IndividualFitPresenter:
    def __init__(self, drops: Sequence[IFTDropAnalysis], view: IndividualFitView) -> None:
        self._drops = drops
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._master = MasterPresenter(drops, self._view.master)
        self._detail = None  # type: Optional[DetailPresenter]

        event_connections = [
            self._master.bn_selected.on_changed.connect(self._update_detail)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        self._update_detail()

    def _update_detail(self) -> None:
        selected_drop = self._master.bn_selected.get()
        if selected_drop is None:
            return

        self._detail_show_drop(selected_drop)

    def _detail_show_drop(self, drop: IFTDropAnalysis) -> None:
        if self._detail is not None:
            self._detail.destroy()
            self._detail = None

        self._detail = DetailPresenter(drop, self._view.detail)

    def destroy(self) -> None:
        assert not self.__destroyed

        for f in self.__cleanup_tasks:
            f()

        if self._master:
            self._master.destroy()

        if self._detail:
            self._detail.destroy()

        self.__destroyed = True
