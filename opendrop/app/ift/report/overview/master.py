# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from enum import IntEnum
from typing import Any, Optional, Sequence, cast

from gi.repository import Gtk, GObject
from gi.repository import GLib

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, TemplateChild, component, install


COLUMN_TYPES = (object, int, str, str, str, str, str, str)


class Column(IntEnum):
    STATUS        = 0
    SPINNER_PULSE = 1

    TIMESTAMP     = 2
    IFT           = 3
    VOLUME        = 4
    SURFACE_AREA  = 5
    BOND          = 6
    WORTHINGTON   = 7


@component(
    template_path='./master.ui',
)
class IFTReportOverviewMasterPresenter(Presenter[Gtk.ScrolledWindow]):
    tree_view = TemplateChild('tree_view')  # type: TemplateChild[Gtk.TreeView]
    tree_selection = TemplateChild('tree_selection')  # type: TemplateChild[Gtk.TreeSelection]

    _initial_selection = None
    _analyses = ()

    view_ready = False

    def __init__(self) -> None:
        self.model = Gtk.ListStore(*COLUMN_TYPES)
        self.row_bindings = []
        self.ignore_tree_selection_changes = False

    def after_view_init(self) -> None:
        self.tree_view.set_model(self.model)

        time_column = Gtk.TreeViewColumn(title='Time [s]')
        time_column.set_spacing(5)
        self.tree_view.append_column(time_column)

        status_icon = Gtk.CellRendererPixbuf()
        time_column.pack_start(status_icon, False)
        time_column.set_cell_data_func(status_icon, self.status_icon_data_func)

        status_spinner = Gtk.CellRendererSpinner()
        time_column.pack_start(status_spinner, False)
        time_column.set_cell_data_func(status_spinner, self.status_spinner_data_func)

        time_text = Gtk.CellRendererText()
        time_column.pack_start(time_text, True)
        time_column.set_attributes(time_text, text=Column.TIMESTAMP)

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='IFT [mN/m]',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.IFT
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='V [mm³]',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.VOLUME
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='SA [mm²]',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.SURFACE_AREA
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Bond',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.BOND
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Worth.',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.WORTHINGTON
        ))

        self.view_ready = True

        self.analyses_changed()

        self.selection = self._initial_selection

    def status_icon_data_func(
            self,
            tree_column: Gtk.TreeViewColumn,
            cell: Gtk.CellRendererPixbuf,
            tree_model: Gtk.TreeModel,
            tree_iter: Gtk.TreeIter,
            data: Any,
    ) -> None:
        status = tree_model.get_value(tree_iter, Column.STATUS)

        if status is PendantAnalysisJob.Status.WAITING_FOR_IMAGE:
            cell.props.icon_name = 'image-loading'
            cell.props.visible = True
        elif status is PendantAnalysisJob.Status.CANCELLED:
            cell.props.icon_name = 'process-stop'
            cell.props.visible = True
        elif status is not PendantAnalysisJob.Status.FITTING:
            cell.props.icon_name = ''
            cell.props.visible = True
        else:
            cell.props.visible = False

    def status_spinner_data_func(
            self,
            tree_column: Gtk.TreeViewColumn,
            cell: Gtk.CellRendererPixbuf,
            tree_model: Gtk.TreeModel,
            tree_iter: Gtk.TreeIter,
            data: Any,
    ) -> None:
        status = tree_model.get_value(tree_iter, Column.STATUS)
        pulse = tree_model.get_value(tree_iter, Column.SPINNER_PULSE)

        if status is PendantAnalysisJob.Status.FITTING:
            cell.props.active = True
            cell.props.pulse = pulse
            cell.props.visible = True
        else:
            cell.props.active = False
            cell.props.visible = False

    @install
    @GObject.Property
    def selection(self) -> Optional[PendantAnalysisJob]:
        if not self.view_ready:
            return self._initial_selection

        _, tree_iter = self.tree_selection.get_selected()
        if tree_iter is None:
            return None

        row = Gtk.TreeRowReference(
            model=self.model,
            path=self.model.get_path(tree_iter)
        )

        for p in self.row_bindings:
            if p.row.get_path() == row.get_path():
                return p.analysis
        else:
            raise RuntimeError

    @selection.setter
    def selection(self, analysis: Optional[PendantAnalysisJob]) -> None:
        if not self.view_ready:
            self._initial_selection = analysis

        if self.selection == analysis:
            return

        self.ignore_tree_selection_changes = True
        try:
            if analysis is not None:
                for binding in self.row_bindings:
                    if binding.analysis == analysis:
                        break
                else:
                    raise ValueError

                self.tree_selection.select_path(binding.row.get_path())
            else:
                self.tree_selection.unselect_all()
        finally:
            self.ignore_tree_selection_changes = False

    @install
    @GObject.Property
    def analyses(self) -> Sequence[PendantAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Sequence[PendantAnalysisJob]) -> None:
        self._analyses = tuple(value)
        if self.view_ready:
            self.analyses_changed()

    def analyses_changed(self) -> None:
        analyses = self.analyses
        bound = [p.analysis for p in self.row_bindings]

        for analysis in analyses:
            if analysis in bound: continue
            self.bind_analysis(analysis)

        for analysis in bound:
            if analysis in analyses: continue
            self.unbind_analysis(analysis)

    def bind_analysis(self, analysis: PendantAnalysisJob) -> None:
        row = self.new_model_row()

        new_binding = RowBinding(analysis, row)
        self.row_bindings.append(new_binding)

        if self.selection is None:
            self.selection = analysis

    def unbind_analysis(self, analysis: PendantAnalysisJob) -> None:
        for binding in self.row_bindings:
            if binding.analysis == analysis:
                break
        else:
            raise ValueError("analysis not added to this model")

        if self.selection == analysis:
            if len(self.row_bindings) == 1:
                self.selection = None
            else:
                index = self.row_bindings.index(binding)
                if index + 1 < len(self.row_bindings):
                    next_index = index + 1
                else:
                    next_index = index - 1
                self.selection = self.row_bindings[next_index].analysis

        self.row_bindings.remove(binding)
        binding.unbind()

        self.remove_model_row(binding.row)

    def new_model_row(self) -> Gtk.TreeRowReference:
        tree_iter = self.model.append((None,) * len(Column))
        row = Gtk.TreeRowReference(
            model=self.model,
            path=self.model.get_path(tree_iter)
        )

        self.host.queue_resize()
        self.tree_view.queue_resize()
        self.tree_view.queue_allocate()

        return row

    def remove_model_row(self, row: Gtk.TreeRowReference) -> None:
        tree_iter = self.model.get_iter(row.get_path())
        self.model.remove(tree_iter)

    def tree_selection_changed(self, tree_selection: Gtk.TreeSelection) -> None:
        if self.ignore_tree_selection_changes:
            return
        self.notify('selection')


class RowBinding:
    def __init__(self, analysis: PendantAnalysisJob, row: Gtk.TreeRowReference) -> None:
        self.analysis = analysis
        self.row = row

        self._spinner_pulse = 0
        self._spinner_animation_timer = None

        self._analysis_status_changed_connection = \
            analysis.bn_status.on_changed.connect(
                self._update_row
            )

        self._update_row()

    def _update_row(self) -> None:
        status = self.analysis.bn_status.get()
        timestamp = self.analysis.bn_image_timestamp.get()
        ift = 1e3 * self.analysis.bn_interfacial_tension.get()
        volume = 1e9 * self.analysis.bn_volume.get()
        surface_area = 1e6 * self.analysis.bn_surface_area.get()
        bond = self.analysis.bn_bond_number.get()
        worthington = self.analysis.bn_worthington.get()
        
        data = {
            Column.STATUS: status,
            Column.TIMESTAMP: f'{timestamp:.1f}',
            Column.IFT: f'{ift:.4g}',
            Column.VOLUME: f'{volume:.4g}',
            Column.SURFACE_AREA: f'{surface_area:.4g}',
            Column.BOND: f'{bond:.4g}',
            Column.WORTHINGTON: f'{worthington:.4g}',
        }

        self._model.set(self._iter, list(data.keys()), list(data.values()))

        if status is PendantAnalysisJob.Status.FITTING and self._spinner_animation_timer is None:
            self._spinner_animation_timer = GLib.timeout_add(
                priority=GLib.PRIORITY_LOW,
                interval=750//12,
                function=self._spinner_animation_step
            )

    def _spinner_animation_step(self) -> bool:
        status = self.analysis.bn_status.get()
        if status is PendantAnalysisJob.Status.FITTING:
            self._spinner_pulse += 1
            self._spinner_pulse %= 12
            self._model.set(self._iter, Column.SPINNER_PULSE, self._spinner_pulse)
            return GLib.SOURCE_CONTINUE
        else:
            self._spinner_animation_timer = None
            return GLib.SOURCE_REMOVE

    @property
    def _iter(self) -> Gtk.TreeIter:
        return self._model.get_iter(self.row.get_path())

    @property
    def _model(self) -> Gtk.ListStore:
        return cast(Gtk.ListStore, self.row.get_model())

    def unbind(self) -> None:
        self._analysis_status_changed_connection.disconnect()
