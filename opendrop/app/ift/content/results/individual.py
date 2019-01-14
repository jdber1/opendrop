import functools
from typing import MutableSequence, Optional

import numpy as np
from gi.repository import Gtk, Pango, Gdk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindableAdapter


class DetailView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .notebook-small-tabs tab {
         padding: 0px;
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

            ift_lbl = Gtk.Label('IFT (mN/m):', xalign=0)
            sheet.attach(ift_lbl, 0, 0, 1, 1)

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

            ift_val = Gtk.Label(xalign=0)
            sheet.attach_next_to(ift_val, ift_lbl, Gtk.PositionType.RIGHT, 1, 1)

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

            self.bn_ift = AtomicBindableAdapter(
                setter=lambda v: ift_val.set_text('{:.4g}'.format(v)))
            self.bn_volume = AtomicBindableAdapter(
                setter=lambda v: volume_val.set_text('{:.4g}'.format(v)))
            self.bn_surface_area = AtomicBindableAdapter(
                setter=lambda v: surface_area_val.set_text('{:.4g}'.format(v)))
            self.bn_worthington = AtomicBindableAdapter(
                setter=lambda v: worthington_val.set_text('{:.4g}'.format(v)))
            self.bn_bond_number = AtomicBindableAdapter(
                setter=lambda v: bond_number_val.set_text('{:.4g}'.format(v)))
            self.bn_apex_coords = AtomicBindableAdapter(
                setter=lambda v: apex_coords_val.set_text('({0[0]:.4g}, {0[1]:.4g})'.format(v)))
            self.bn_image_angle = AtomicBindableAdapter(
                setter=lambda v: image_angle_val.set_text('{:.4g}°'.format(v)))

    class DropContourAndResidualsView(GtkWidgetView[Gtk.Grid]):
        def __init__(self) -> None:
            self.widget = Gtk.Grid()

            stack = Gtk.Stack()
            self.widget.attach(stack, 0, 0, 1, 1)

            self._drop_figure = Figure(tight_layout=True)
            drop_figure_canvas = FigureCanvas(self._drop_figure)
            drop_figure_canvas.props.hexpand = True
            drop_figure_canvas.props.vexpand = True
            stack.add_titled(drop_figure_canvas, name='Drop', title='Drop')

            self._residuals_figure = Figure(tight_layout=True)
            residuals_figure_canvas = FigureCanvas(self._residuals_figure)
            residuals_figure_canvas.props.hexpand = True
            residuals_figure_canvas.props.vexpand = True
            stack.add_titled(residuals_figure_canvas, name='Residuals', title='Residuals')

            stack_switcher = Gtk.StackSwitcher(stack=stack, halign=Gtk.Align.CENTER, margin_left=10, margin_bottom=10,
                                               margin_right=10)
            self.widget.attach(stack_switcher, 0, 1, 1, 1)
            stack_switcher.get_style_context().add_class('individual-detail-view-stack-switcher')

            self.widget.show_all()

            # Wiring things up

            self._drop_image = None  # type: Optional[Image]
            self._drop_contour = None  # type: Optional[np.ndarray]
            self._drop_contour_fit = None  # type: Optional[np.ndarray]
            self._drop_contour_fit_residuals = None  # type: Optional[np.ndarray]

            self.bn_drop_image = AtomicBindableAdapter(setter=self._set_drop_image)
            self.bn_drop_contour = AtomicBindableAdapter(setter=self._set_drop_contour)
            self.bn_drop_contour_fit = AtomicBindableAdapter(setter=self._set_drop_contour_fit)
            self.bn_drop_contour_fit_residuals = AtomicBindableAdapter(setter=self._set_drop_contour_fit_residuals)

        def _set_drop_image(self, image: Optional[Image]) -> None:
            self._drop_image = image
            self._draw_drop()

        def _set_drop_contour(self, contour: Optional[np.ndarray]) -> None:
            self._drop_contour = contour
            self._draw_drop()

        def _set_drop_contour_fit(self, contour: Optional[np.ndarray]) -> None:
            self._drop_contour_fit = contour
            self._draw_drop()

        def _set_drop_contour_fit_residuals(self, residuals: Optional[np.ndarray]) -> None:
            self._drop_contour_fit_residuals = residuals
            self._draw_residuals()

        def _draw_drop(self) -> None:
            self._drop_figure.clear()

            drop_image = self._drop_image
            drop_contour = self._drop_contour
            drop_contour_fit = self._drop_contour_fit
            if drop_image is None or drop_contour is None or drop_contour_fit is None:
                self._drop_figure.canvas.draw()
                return

            drop_image_extents = np.array([0, drop_image.shape[1], drop_image.shape[0], 0])

            axes = self._drop_figure.add_subplot(1, 1, 1)
            axes.xaxis.tick_top()

            for item in (axes.get_xticklabels() + axes.get_yticklabels()):
                item.set_fontsize(8)

            axes.imshow(drop_image, origin='upper', extent=drop_image_extents, aspect='equal')

            axes.plot(*drop_contour.T, linestyle='-', color='#0080ff', linewidth=1.5)
            axes.plot(*drop_contour_fit.T, linestyle='-', color='#ff0080', linewidth=1)

            # Reset the limits as they may have been modified during the plotting of various contours
            axes.set_xlim(drop_image_extents[:2])
            axes.set_ylim(drop_image_extents[2:])

            self._drop_figure.canvas.draw()

        def _draw_residuals(self):
            self._residuals_figure.clear()

            residuals = self._drop_contour_fit_residuals
            if residuals is None:
                self._drop_figure.canvas.draw()
                return

            axes = self._residuals_figure.add_subplot(1, 1, 1)

            for item in (axes.get_xticklabels() + axes.get_yticklabels()):
                item.set_fontsize(8)

            axes.plot(residuals[:, 0], residuals[:, 1], color='#0080ff', marker='o', linestyle='')

            self._residuals_figure.canvas.draw()

    class LogView(GtkWidgetView[Gtk.ScrolledWindow]):
        def __init__(self) -> None:
            self.widget = Gtk.ScrolledWindow()
            log_text_view = Gtk.TextView(monospace=True, editable=False, wrap_mode=Gtk.WrapMode.CHAR, hexpand=True,
                                         vexpand=True, margin=10)
            self.widget.add(log_text_view)
            self.widget.show_all()

            # Wiring things up

            self.bn_log_text = AtomicBindableAdapter(setter=lambda v: log_text_view.get_buffer().set_text(v))


    def __init__(self) -> None:
        self.widget = Gtk.Grid(margin=10, column_spacing=10)

        self.parameters = self.ParametersView()
        self.widget.attach(self.parameters.widget, 0, 0, 1, 1)

        notebook = Gtk.Notebook(hexpand=True, vexpand=True)
        notebook.get_style_context().add_class('notebook-small-tabs')
        self.widget.attach(notebook, 1, 0, 1, 1)

        self.drop_contour_and_residuals = self.DropContourAndResidualsView()
        notebook.append_page(self.drop_contour_and_residuals.widget, Gtk.Label('Drop contour'))

        self.log = self.LogView()
        notebook.append_page(self.log.widget, Gtk.Label('Log'))

        self.widget.show_all()


class MasterView(GtkWidgetView[Gtk.Grid]):
    class Row:
        STATUS_COL = 1
        LOG_COL = 2

        def __init__(self, model: Gtk.ListStore, row_ref: Gtk.TreeRowReference) -> None:
            self._model = model
            self._row_ref = row_ref

            self.bn_selected = AtomicBindableVar(False)

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

    def clear(self) -> None:
        self._rows = []
        self.fits.clear()

    def new_row(self) -> 'MasterView.Row':
        num_rows = self.fits.iter_n_children()
        frame_num = num_rows + 1

        tree_iter = self.fits.append((frame_num, None, None))
        row_ref = Gtk.TreeRowReference(model=self.fits, path=self.fits.get_path(tree_iter))
        row = self.Row(self.fits, row_ref)
        row.bn_selected.on_changed.connect(functools.partial(self._hdl_row_selected_changed, row), strong_ref=True,
                                           immediate=True)
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

        row = self._get_row_from_tree_iter(tree_iter)

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
