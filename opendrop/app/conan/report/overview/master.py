# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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
import math
from typing import Any, Optional, Sequence, cast

from gi.repository import Gtk, GObject, GLib

from opendrop.app.conan.services.analysis import ConanAnalysisJob, ConanAnalysisStatus
from opendrop.appfw import Presenter, TemplateChild, component, install


COLUMN_TYPES = (object, int, str, str, str)

class Column(IntEnum):
    STATUS        = 0
    SPINNER_PULSE = 1

    TIMESTAMP     = 2
    LEFT_CA       = 3
    RIGHT_CA      = 4


@component(
    template_path='./master.ui',
)
class ConanReportOverviewMasterPresenter(Presenter):
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
            title='Left CA [°]',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.LEFT_CA))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Right CA [°]',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.RIGHT_CA
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

        if status is ConanAnalysisStatus.WAITING_FOR_IMAGE:
            cell.props.icon_name = 'image-loading'
            cell.props.visible = True
        elif status is ConanAnalysisStatus.CANCELLED:
            cell.props.icon_name = 'process-stop'
            cell.props.visible = True
        elif status is not ConanAnalysisStatus.FITTING:
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

        if status is ConanAnalysisStatus.FITTING:
            cell.props.active = True
            cell.props.pulse = pulse
            cell.props.visible = True
        else:
            cell.props.active = False
            cell.props.visible = False

    @install
    @GObject.Property
    def selection(self) -> Optional[ConanAnalysisJob]:
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
    def selection(self, selection: Optional[ConanAnalysisJob]) -> None:
        if not self.view_ready:
            self._initial_selection = selection

        if self.selection == selection:
            return

        self.ignore_tree_selection_changes = True
        try:
            if selection is not None:
                for p in self.row_bindings:
                    if p.analysis == selection:
                        row_bindings = p
                        break
                else:
                    raise ValueError

                self.tree_selection.select_path(row_bindings.row.get_path())
            else:
                self.tree_selection.unselect_all()
        finally:
            self.ignore_tree_selection_changes = False

    @install
    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Sequence[ConanAnalysisJob]) -> None:
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

    def bind_analysis(self, analysis: ConanAnalysisJob) -> None:
        row = self.new_model_row()

        new_binding = RowBinding(analysis, row)
        self.row_bindings.append(new_binding)

        if self.selection is None:
            self.selection = analysis

    def unbind_analysis(self, analysis: ConanAnalysisJob) -> None:
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
    def __init__(self, analysis: ConanAnalysisJob, row: Gtk.TreeRowReference) -> None:
        self.analysis = analysis
        self.row = row

        self._spinner_pulse = 0
        self._spinner_animation_timer = None

        self._analysis_status_changed_id = analysis.connect('notify::status', self._update_row)

        self._update_row()

    def _update_row(self, *_) -> None:
        status = self.analysis.status
        timestamp = self.analysis.timestamp
        left_ca = self.analysis.left_angle
        right_ca = self.analysis.right_angle

        if timestamp is not None:
            timestamp_txt = f'{timestamp:.1f}'
        else:
            timestamp_txt = ''

        if left_ca is not None:
            left_ca_txt = f'{math.degrees(left_ca):.3g}'
        else:
            left_ca_txt = ''

        if right_ca is not None:
            right_ca_txt = f'{math.degrees(right_ca):.3g}'
        else:
            right_ca_txt = ''

        data = {
            Column.STATUS: status,
            Column.TIMESTAMP: timestamp_txt,
            Column.LEFT_CA: left_ca_txt,
            Column.RIGHT_CA: right_ca_txt,
        }

        self._model.set(self._iter, list(data.keys()), list(data.values()))

        if status is ConanAnalysisStatus.FITTING and self._spinner_animation_timer is None:
            self._spinner_animation_timer = GLib.timeout_add(
                priority=GLib.PRIORITY_LOW,
                interval=750//12,
                function=self._spinner_animation_step
            )

    def _spinner_animation_step(self) -> bool:
        if self.analysis.status is ConanAnalysisStatus.FITTING:
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
        self.analysis.disconnect(self._analysis_status_changed_id)
