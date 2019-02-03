import functools
import math
from typing import MutableSequence, Optional, Sequence, MutableMapping, Callable

from gi.repository import Gtk, Gdk, GObject

from opendrop.app.common.content.image_processing.stage import StageView
from opendrop.app.conan.model.analyser import ConanDropAnalysis
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.widgets.render import Render
from opendrop.widgets.render.objects import Angle, Line, Polyline


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

    def __init__(self) -> None:
        self.widget = Gtk.Stack(margin=10)

        self._visualize = Render()
        self.widget.add(self._visualize)

        stage = StageView(render=self._visualize)
        self.bn_drop_image = stage.bn_canvas_source

        surface_line_ro = Line(stroke_color=(0.25, 1.0, 0.25))
        self._visualize.add_render_object(surface_line_ro)
        self.bn_surface_line = GObjectPropertyBindable(surface_line_ro, 'line')

        drop_contour_ro = Polyline(stroke_color=(0.0, 0.5, 1.0))
        self._visualize.add_render_object(drop_contour_ro)
        self.bn_drop_contours = GObjectPropertyBindable(drop_contour_ro, 'polyline')

        left_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5), clockwise=True)
        self._visualize.add_render_object(left_angle_ro)

        self.bn_left_angle = GObjectPropertyBindable(left_angle_ro, 'delta-angle',
                                                     transform_to=lambda angle: -angle,
                                                     transform_from=lambda angle: -angle)
        self.bn_left_point = GObjectPropertyBindable(left_angle_ro, 'vertex-pos')

        surface_line_ro.bind_property(
            'line',
            left_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: math.pi - (math.atan(line.gradient) if line is not None else 0))

        right_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5))
        self._visualize.add_render_object(right_angle_ro)

        self.bn_right_angle = GObjectPropertyBindable(right_angle_ro, 'delta-angle')
        self.bn_right_point = GObjectPropertyBindable(right_angle_ro, 'vertex-pos')

        surface_line_ro.bind_property(
            'line',
            right_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: -math.atan(line.gradient) if line is not None else 0)

        self._waiting_for_data_placeholder_lbl = Gtk.Label()
        self._waiting_for_data_placeholder_lbl.set_markup('<b>Waiting for data...</b>')
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
            self.widget.set_visible_child(self._visualize)

        self._is_waiting_for_data = is_waiting


class MasterView(GtkWidgetView[Gtk.Grid]):
    class Row:
        STATUS_COL = 1
        LEFT_ANGLE_COL = 2
        RIGHT_ANGLE_COL = 3

        def __init__(self, model: Gtk.ListStore, row_ref: Gtk.TreeRowReference) -> None:
            self._model = model
            self._row_ref = row_ref

            self.bn_selected = AtomicBindableVar(False)

        status_text = property()

        @status_text.setter
        def status_text(self, text: str) -> None:
            self._model.set_value(self._get_tree_iter(), column=self.STATUS_COL, value=text)

        left_angle = property()

        @left_angle.setter
        def left_angle(self, angle: float) -> None:
            self._model.set_value(self._get_tree_iter(), column=self.LEFT_ANGLE_COL, value=self._format_angle(angle))

        right_angle = property()

        @right_angle.setter
        def right_angle(self, angle: float) -> None:
            self._model.set_value(self._get_tree_iter(), column=self.RIGHT_ANGLE_COL, value=self._format_angle(angle))

        def _format_angle(self, angle: float) -> str:
            return '{:.4g}°'.format(math.degrees(angle))

        def _get_tree_iter(self) -> Gtk.TreeIter:
            return self._model.get_iter(self._row_ref.get_path())

    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        self._rows = []  # type: MutableSequence[MasterView.Row]
        self._rows_cleanup_tasks = []  # type: MutableSequence[Callable]

        overview_lbl = Gtk.Label(xalign=0, margin=5)
        overview_lbl.set_markup('<b>Overview</b>')
        self.widget.attach(overview_lbl, 0, 0, 1, 1)

        self.fits = Gtk.ListStore(int, str, str, str)

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

        left_angle_col = Gtk.TreeViewColumn('Left angle', Gtk.CellRendererText(), text=2)
        fits_view.append_column(left_angle_col)

        right_angle_col = Gtk.TreeViewColumn('Right angle', Gtk.CellRendererText(), text=3)
        fits_view.append_column(right_angle_col)

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

        tree_iter = self.fits.append((frame_num, None, None, None))
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
    def __init__(self, drop: ConanDropAnalysis, view: DetailView) -> None:
        self._drop = drop
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        data_bindings = [
            drop.bn_left_angle.bind_to(self._view.bn_left_angle),
            drop.bn_left_point.bind_to(self._view.bn_left_point),
            drop.bn_right_angle.bind_to(self._view.bn_right_angle),
            drop.bn_right_point.bind_to(self._view.bn_right_point),
        ]
        self.__cleanup_tasks.extend([db.unbind for db in data_bindings])

        event_connections = [
            self._drop.bn_status.on_changed.connect(self._hdl_drop_status_changed),
            self._drop.bn_image_annotations.on_changed.connect(self._hdl_image_annotations_changed)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        self._hdl_drop_status_changed()
        self._hdl_image_annotations_changed()

    def _hdl_drop_status_changed(self) -> None:
        status = self._drop.status
        self._view.is_waiting_for_data = (status is ConanDropAnalysis.Status.WAITING_FOR_IMAGE or
                                          status is ConanDropAnalysis.Status.READY_TO_FIT)

    def _hdl_image_annotations_changed(self) -> None:
        image_annotations = self._drop.image_annotations

        if image_annotations is None:
            image = None
            drop_contours_px = []
            surface_line_px = None
        else:
            image = self._drop.image
            drop_contours_px = image_annotations.drop_contours_px
            surface_line_px = image_annotations.surface_line_px

        self._view.bn_drop_image.set(image)
        self._view.bn_drop_contours.set(drop_contours_px)
        self._view.bn_surface_line.set(surface_line_px)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class MasterPresenter:
    def __init__(self, drops: Sequence[ConanDropAnalysis], view: MasterView) -> None:
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._drop_to_row = {}  # type: MutableMapping[ConanDropAnalysis, MasterView.Row]
        self.bn_selected = AtomicBindableVar(None)  # type: AtomicBindable[Optional[ConanDropAnalysis]]

        self._view.clear()
        self.add_drops(drops)

        # Only show an overview if more than one drop analysis.
        self._view.visible = len(drops) > 1

    def add_drops(self, drops: Sequence[ConanDropAnalysis]) -> None:
        for drop in drops:
            self.add_drop(drop)

    def add_drop(self, drop: ConanDropAnalysis) -> None:
        row = self._view.new_row()
        self._drop_to_row[drop] = row

        event_connections = [
            drop.bn_status.on_changed.connect(functools.partial(self._update_row_status_text, row, drop),
                                              weak_ref=False),
            drop.bn_left_angle.on_changed.connect(functools.partial(self._update_row_left_angle, row, drop),
                                                  weak_ref=False),
            drop.bn_right_angle.on_changed.connect(functools.partial(self._update_row_right_angle, row, drop),
                                                   weak_ref=False),
            row.bn_selected.on_changed.connect(functools.partial(self._hdl_row_selected_changed, row), weak_ref=False)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        self._update_row_status_text(row, drop)
        self._update_row_left_angle(row, drop)
        self._update_row_right_angle(row, drop)
        self._hdl_row_selected_changed(row)

    def _update_row_status_text(self, row: MasterView.Row, drop: ConanDropAnalysis) -> None:
        row.status_text = str(drop.status)

    def _update_row_left_angle(self, row: MasterView.Row, drop: ConanDropAnalysis) -> None:
        row.left_angle = drop.bn_left_angle.get()

    def _update_row_right_angle(self, row: MasterView.Row, drop: ConanDropAnalysis) -> None:
        row.right_angle = drop.bn_right_angle.get()

    def _hdl_row_selected_changed(self, row: MasterView.Row) -> None:
        if not row.bn_selected.get():
            return

        drop = self._drop_from_row(row)
        self.bn_selected.set(drop)

    def _drop_from_row(self, row: MasterView.Row) -> ConanDropAnalysis:
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
    def __init__(self, drops: Sequence[ConanDropAnalysis], view: IndividualFitView) -> None:
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

    def _detail_show_drop(self, drop: ConanDropAnalysis) -> None:
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
