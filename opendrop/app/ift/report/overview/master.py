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


from typing import Optional, Sequence

from gi.repository import Gtk, Pango, GObject

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import componentclass, TemplateChild


@componentclass(
    template_path='./master.ui',
)
class IFTReportOverviewMaster(Gtk.ScrolledWindow):
    __gtype_name__ = 'IFTReportOverviewMaster'

    _tree_view = TemplateChild('tree_view')
    _tree_model = TemplateChild('tree_model')
    _tree_selection = TemplateChild('tree_selection')

    _initial_selection = None
    _analyses = ()

    _template_ready = False

    class _RowPresenter:
        TIMESTAMP_COL = 0
        STATUS_COL = 1
        LOG_TEXT_COL = 2

        def __init__(self, row_ref: Gtk.TreeRowReference, analysis: IFTDropAnalysis) -> None:
            self.analysis = analysis
            self.row_ref = row_ref

            self._event_connections = [
                analysis.bn_image_timestamp.on_changed.connect(
                    self._update_timestamp
                ),
                analysis.bn_status.on_changed.connect(
                    self._update_status_text
                ),
                analysis.bn_log.on_changed.connect(
                    self._update_log_text
                ),
            ]

            self._update_timestamp()
            self._update_status_text()
            self._update_log_text()

        def _update_timestamp(self) -> None:
            timestamp = self.analysis.bn_image_timestamp.get()
            text = format(timestamp, '.1f')
            self._tree_model.set_value(self._tree_iter, column=self.TIMESTAMP_COL, value=text)

        def _update_status_text(self) -> None:
            status = self.analysis.bn_status.get()
            text = status.display_name
            self._tree_model.set_value(self._tree_iter, column=self.STATUS_COL, value=text)

        def _update_log_text(self) -> None:
            log_history = self.analysis.bn_log.get()
            log_lines = log_history.splitlines()

            text = log_lines[-1] if log_lines else ''
            self._tree_model.set_value(self._tree_iter, column=self.LOG_TEXT_COL, value=text)

        @property
        def _tree_iter(self) -> Gtk.TreeIter:
            return self._tree_model.get_iter(self.row_ref.get_path())

        @property
        def _tree_model(self) -> Gtk.TreeModel:
            return self.row_ref.get_model()

        def destroy(self) -> None:
            for conn in self._event_connections:
                conn.disconnect()

    def after_template_init(self) -> None:
        self._row_presenters = []
        self._ignore_tree_selection_changes = False

        self._tree_view.append_column(Gtk.TreeViewColumn(
            title='Timestamp (s)',
            cell_renderer=Gtk.CellRendererText(),
            text=0
        ))

        self._tree_view.append_column(Gtk.TreeViewColumn(
            title='Status',
            cell_renderer=Gtk.CellRendererText(),
            text=1
        ))

        self._tree_view.append_column(Gtk.TreeViewColumn(
            title='Log',
            cell_renderer=Gtk.CellRendererText(
                font='Monospace',
                ellipsize=Pango.EllipsizeMode.END
            ),
            text=2
        ))

        self._hdl_analyses_changed()
        self.selection = self._initial_selection

        self._template_ready = True

    @GObject.Property
    def selection(self) -> Optional[IFTDropAnalysis]:
        if not self._template_ready:
            return self._initial_selection

        _, tree_iter = self._tree_selection.get_selected()
        if tree_iter is None:
            return None

        row_ref = Gtk.TreeRowReference(
            model=self._tree_model,
            path=self._tree_model.get_path(tree_iter)
        )

        for p in self._row_presenters:
            if p.row_ref.get_path() == row_ref.get_path():
                return p.analysis
        else:
            raise RuntimeError

    @selection.setter
    def selection(self, analysis: Optional[IFTDropAnalysis]) -> None:
        if type(analysis) is not IFTDropAnalysis and analysis is not None:
            breakpoint()
        if not self._template_ready:
            self._initial_selection = analysis

        if self.selection == analysis:
            return

        self._ignore_tree_selection_changes = True
        try:
            if analysis is not None:
                for p in self._row_presenters:
                    if p.analysis == analysis:
                        row_presenter = p
                        break
                else:
                    raise ValueError

                self._tree_selection.select_path(row_presenter.row_ref.get_path())
            else:
                self._tree_selection.unselect_all()
        finally:
            self._ignore_tree_selection_changes = False

    @GObject.Property
    def analyses(self) -> Sequence[IFTDropAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Sequence[IFTDropAnalysis]) -> None:
        self._analyses = tuple(value)
        if self._template_ready:
            self._hdl_analyses_changed()

    def _hdl_analyses_changed(self) -> None:
        current = [p.analysis for p in self._row_presenters]
        new = self.analyses

        # Add new analyses in the same order as they appear in 'value'.
        to_show = [
            analysis
            for analysis in new if analysis not in current
        ]
        for a in to_show:
            self._add_analysis(a)

        to_remove = set(current) - set(new)
        for a in to_remove:
            self._remove_analysis(a)

    def _add_analysis(self, analysis: IFTDropAnalysis) -> None:
        row_ref = self._new_row()

        row_presenter = self._RowPresenter(row_ref, analysis)
        self._row_presenters.append(row_presenter)

        if self.selection is None:
            self.selection = analysis

    def _remove_analysis(self, analysis: IFTDropAnalysis) -> None:
        for p in self._row_presenters:
            if p.analysis == analysis:
                row_presenter = p
                break
        else:
            raise ValueError("analysis not added to this model")

        if self.selection == analysis:
            next_selection = None
            if len(self._row_presenters) > 1:
                row_presenter_index = self._row_presenters.index(row_presenter)
                if row_presenter_index + 1 < len(self._row_presenters):
                    next_selection = self._row_presenters[row_presenter_index + 1].analysis
                else:
                    next_selection = self._row_presenters[row_presenter_index - 1].analysis
            self.selection = next_selection

        self._row_presenters.remove(row_presenter)
        row_presenter.destroy()

        self._remove_row(row_presenter.row_ref)

    def _new_row(self) -> Gtk.TreeRowReference:
        tree_iter = self._tree_model.append((None, None, None))
        row_ref = Gtk.TreeRowReference(
            model=self._tree_model,
            path=self._tree_model.get_path(tree_iter)
        )

        self.queue_resize()
        self._tree_view.queue_resize()
        self._tree_view.queue_allocate()
        self._tree_view.queue_allocate()

        return row_ref

    def _remove_row(self, row_ref: Gtk.TreeRowReference) -> None:
        tree_iter = self._tree_model.get_iter(row_ref.get_path())
        self._tree_model.remove(tree_iter)

    def _hdl_tree_selection_changed(self, tree_selection: Gtk.TreeSelection) -> None:
        if self._ignore_tree_selection_changes:
            return
        self.notify('selection')
