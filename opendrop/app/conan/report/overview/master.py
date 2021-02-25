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


import math
from typing import Optional, Sequence

from gi.repository import Gtk, GObject

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.appfw import Presenter, TemplateChild, component, install


@component(
    template_path='./master.ui',
)
class ConanReportOverviewMasterPresenter(Presenter):
    tree_view = TemplateChild('tree_view')  # type: TemplateChild[Gtk.TreeView]
    tree_model = TemplateChild('tree_model')  # type: TemplateChild[Gtk.ListStore]
    tree_selection = TemplateChild('tree_selection')  # type: TemplateChild[Gtk.TreeSelection]

    _initial_selection = None
    _analyses = ()

    view_ready = False

    class _RowPresenter:
        TIMESTAMP_COL = 0
        STATUS_COL = 1
        LEFT_ANGLE_COL = 2
        RIGHT_ANGLE_COL = 3

        def __init__(self, row_ref: Gtk.TreeRowReference, analysis: ConanAnalysis) -> None:
            self.row_ref = row_ref
            self.analysis = analysis

            self._event_connections = [
                analysis.bn_image_timestamp.on_changed.connect(
                    self._update_timestamp
                ),
                analysis.bn_status.on_changed.connect(
                    self._update_status_text
                ),
                analysis.bn_left_angle.on_changed.connect(
                    self._update_left_angle
                ),
                analysis.bn_right_angle.on_changed.connect(
                    self._update_right_angle
                ),
            ]

            self._update_timestamp()
            self._update_status_text()
            self._update_left_angle()
            self._update_right_angle()

        def _update_timestamp(self) -> None:
            timestamp = self.analysis.bn_image_timestamp.get()
            text = format(timestamp, '.1f')
            self._tree_model.set_value(self._tree_iter, column=self.TIMESTAMP_COL, value=text)

        def _update_status_text(self) -> None:
            status = self.analysis.bn_status.get()
            text = status.display_name
            self._tree_model.set_value(self._tree_iter, column=self.STATUS_COL, value=text)

        def _update_left_angle(self) -> None:
            left_angle = self.analysis.bn_left_angle.get()
            if left_angle is not None and math.isfinite(left_angle):
                text = format(math.degrees(left_angle), '.1f')
            else:
                text = ''
            self._tree_model.set_value(self._tree_iter, column=self.LEFT_ANGLE_COL, value=text)

        def _update_right_angle(self) -> None:
            right_angle = self.analysis.bn_right_angle.get()
            if right_angle is not None and math.isfinite(right_angle):
                text = format(math.degrees(right_angle), '.1f')
            else:
                text = ''
            self._tree_model.set_value(self._tree_iter, column=self.RIGHT_ANGLE_COL, value=text)

        @property
        def _tree_iter(self) -> Gtk.TreeIter:
            return self._tree_model.get_iter(self.row_ref.get_path())

        @property
        def _tree_model(self) -> Gtk.TreeModel:
            return self.row_ref.get_model()

        def destroy(self) -> None:
            for conn in self._event_connections:
                conn.disconnect()

    def after_view_init(self) -> None:
        self.row_presenters = []
        self.ignore_tree_selection_changes = False

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Time [s]',
            cell_renderer=Gtk.CellRendererText(),
            text=0,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Status',
            cell_renderer=Gtk.CellRendererText(),
            text=1,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Left [°]',
            cell_renderer=Gtk.CellRendererText(),
            text=2,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Right [°]',
            cell_renderer=Gtk.CellRendererText(),
            text=3,
        ))

        self.view_ready = True
        self.analyses_changed()
        self.selection = self.selection

    @install
    @GObject.Property
    def selection(self) -> Optional[ConanAnalysis]:
        if not self.view_ready:
            return self._initial_selection

        _, tree_iter = self.tree_selection.get_selected()
        if tree_iter is None:
            return None

        row_ref = Gtk.TreeRowReference(
            model=self.tree_model,
            path=self.tree_model.get_path(tree_iter)
        )

        for p in self.row_presenters:
            if p.row_ref.get_path() == row_ref.get_path():
                return p.analysis
        else:
            raise RuntimeError

    @selection.setter
    def selection(self, selection: Optional[ConanAnalysis]) -> None:
        if not self.view_ready:
            self._initial_selection = selection

        if self.selection == selection:
            return

        self.ignore_tree_selection_changes = True
        try:
            if selection is not None:
                for p in self.row_presenters:
                    if p.analysis == selection:
                        row_presenter = p
                        break
                else:
                    raise ValueError

                self.tree_selection.select_path(row_presenter.row_ref.get_path())
            else:
                self.tree_selection.unselect_all()
        finally:
            self.ignore_tree_selection_changes = False

    @install
    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Sequence[ConanAnalysis]) -> None:
        self._analyses = tuple(value)
        if self.view_ready:
            self.analyses_changed()

    def analyses_changed(self) -> None:
        current = [p.analysis for p in self.row_presenters]
        new = self.analyses

        to_show = [
            analysis
            for analysis in new if analysis not in current
        ]
        for a in to_show:
            self.add_analysis(a)

        to_remove = set(current) - set(new)
        for a in to_remove:
            self.remove_analysis(a)

    def add_analysis(self, analysis: ConanAnalysis) -> None:
        row_ref = self.new_row()

        row_presenter = self._RowPresenter(row_ref, analysis)
        self.row_presenters.append(row_presenter)

        if self.selection is None:
            self.selection = analysis

    def remove_analysis(self, analysis: ConanAnalysis) -> None:
        for p in self.row_presenters:
            if p.analysis == analysis:
                row_presenter = p
                break
        else:
            raise ValueError("analysis not added to this model")

        if self.selection == analysis:
            next_selection = None
            if len(self.row_presenters) > 1:
                row_presenter_index = self.row_presenters.index(row_presenter)
                if row_presenter_index + 1 < len(self.row_presenters):
                    next_selection = self.row_presenters[row_presenter_index + 1].analysis
                else:
                    next_selection = self.row_presenters[row_presenter_index - 1].analysis
            self.selection = next_selection

        self.row_presenters.remove(row_presenter)
        row_presenter.destroy()

        self.remove_row(row_presenter.row_ref)

    def new_row(self) -> Gtk.TreeRowReference:
        tree_iter = self.tree_model.append((None, None, None, None))
        row_ref = Gtk.TreeRowReference(
            model=self.tree_model,
            path=self.tree_model.get_path(tree_iter)
        )

        self.host.queue_resize()
        self.tree_view.queue_resize()
        self.tree_view.queue_allocate()

        return row_ref

    def remove_row(self, row_ref: Gtk.TreeRowReference) -> None:
        tree_iter = self.tree_model.get_iter(row_ref.get_path())
        self.tree_model.remove(tree_iter)

    def tree_selection_changed(self, tree_selection: Gtk.TreeSelection) -> None:
        if self.ignore_tree_selection_changes: return
        self.notify('selection')
