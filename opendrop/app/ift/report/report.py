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


from gi.repository import Gtk

from opendrop.app.ift.services.report import IFTReportService
from opendrop.appfw import Inject, Injector, TemplateChild, componentclass

from .overview import IFTReportOverview
from .graphs import IFTReportGraphs


@componentclass(
    template_path='./report.ui',
)
class IFTReport(Gtk.Grid):
    __gtype_name__ = 'IFTReport'

    _frame = TemplateChild('frame')
    _stack = TemplateChild('stack')
    _stack_switcher = TemplateChild('stack_switcher')

    _report = Inject(IFTReportService)
    _injector = Inject(Injector)

    def after_template_init(self) -> None:
        self._overview = self._injector.create_object(IFTReportOverview, additional_kwargs={'visible': True})
        self._stack.add_titled(self._overview, name='Individual Fit', title='Individual Fit')

        graphs = self._injector.create_object(IFTReportGraphs, additional_kwargs={'visible': True})
        self._stack.add_titled(graphs, name='Graphs', title='Graphs')

        self._stack.props.visible_child = self._overview

        self._report.bn_analyses.on_changed.connect(self._hdl_report_analyses_changed)
        self._hdl_report_analyses_changed()

    def _hdl_report_analyses_changed(self) -> None:
        analyses = self._report.bn_analyses.get()
        if len(analyses) <= 1:
            self.hide_graphs()
        else:
            self.show_graphs()

    def show_graphs(self) -> None:
        self._stack_switcher.show()
        self._frame.set_shadow_type(Gtk.ShadowType.IN)

    def hide_graphs(self) -> None:
        self._stack_switcher.hide()
        self._stack.set_visible_child(self._overview)
        self._frame.set_shadow_type(Gtk.ShadowType.NONE)

#    def show_confirm_cancel_dialog(self) -> None:
#        if self._confirm_cancel_dialog is not None:
#            return
#
#        self._confirm_cancel_dialog = YesNoDialog(
#            parent=self._get_parent_window(),
#            message_format='Confirm cancel analysis?',
#        )
#
#        self._confirm_cancel_dialog.connect('delete-event', lambda *_: True)
#        self._confirm_cancel_dialog.connect('response', self._hdl_confirm_cancel_dialog_response)
#
#        self._confirm_cancel_dialog.show()
#
#    def _hdl_confirm_cancel_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
#        accept = (response == Gtk.ResponseType.YES)
#        self.presenter.hdl_confirm_cancel_response(accept)
#
#    def hide_confirm_cancel_dialog(self) -> None:
#        if self._confirm_cancel_dialog is None:
#            return
#
#        self._confirm_cancel_dialog.destroy()
#        self._confirm_cancel_dialog = None
#
#    def show_confirm_discard_dialog(self) -> None:
#        if self._confirm_discard_dialog is not None:
#            return
#
#        self._confirm_discard_dialog = YesNoDialog(
#            parent=self._get_parent_window(),
#            message_format='Confirm discard results?',
#        )
#
#        self._confirm_discard_dialog.connect('delete-event', lambda *_: True)
#        self._confirm_discard_dialog.connect('response', self._hdl_confirm_discard_dialog_response)
#
#        self._confirm_discard_dialog.show()
#
#    def _hdl_confirm_discard_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
#        accept = (response == Gtk.ResponseType.YES)
#        self.presenter.hdl_confirm_discard_response(accept)
#
#    def hide_confirm_discard_dialog(self) -> None:
#        if self._confirm_discard_dialog is None:
#            return
#
#        self._confirm_discard_dialog.destroy()
#        self._confirm_discard_dialog = None
#
#    def show_save_dialog(self, options: IFTAnalysisSaverOptions) -> None:
#        if self._save_dialog_cid is not None:
#            return
#
#        self._save_dialog_cid, save_dialog = self.new_component(
#            ift_save_dialog_cs.factory(
#                model=options,
#                do_ok=(
#                    lambda: self.presenter.hdl_save_dialog_response(should_save=True)
#                ),
#                do_cancel=(
#                    lambda: self.presenter.hdl_save_dialog_response(should_save=False)
#                ),
#                parent_window=self._get_parent_window(),
#            )
#        )
#        save_dialog.show()
#
#    def hide_save_dialog(self) -> None:
#        if self._save_dialog_cid is None:
#            return
#
#        self.remove_component(self._save_dialog_cid)
#        self._save_dialog_cid = None
#
#    def _get_parent_window(self) -> Optional[Gtk.Window]:
#        toplevel = self._widget.get_toplevel()
#        if isinstance(toplevel, Gtk.Window):
#            return toplevel
#        else:
#            return None
#
#    def _do_destroy(self) -> None:
#        self._widget.destroy()
#        self.hide_confirm_cancel_dialog()
#        self.hide_confirm_discard_dialog()
#
#
#@ift_results_cs.presenter(options=['model', 'page_controls'])
#class IFTResultsPresenter(Presenter['IFTResultsView']):
#    UPDATE_TIME_INTERVAL = 1
#
#    def _do_init(self, model: IFTResultsModel, page_controls: WizardPageControls) -> None:
#        self._loop = asyncio.get_event_loop()
#
#        self._model = model
#        self._page_controls = page_controls
#
#        self.individual_model = model.individual
#        self.graphs_model = model.graphs
#
#        self.bn_footer_status = VariableBindable(ResultsFooterStatus.IN_PROGRESS)
#        self.bn_completion_progress = model.bn_analyses_completion_progress
#        self.bn_time_elapsed = VariableBindable(math.nan)
#        self.bn_time_remaining = VariableBindable(math.nan)
#
#        self._active_save_options = None
#
#        self.__event_connections = [
#            model.bn_analyses_time_start.on_changed.connect(
#                self._update_times
#            ),
#            model.bn_analyses_time_est_complete.on_changed.connect(
#                self._update_times
#            ),
#        ]
#
#        self._update_times()
#
#    def view_ready(self) -> None:
#        self.__event_connections.extend([
#            self._model.bn_fitting_status.on_changed.connect(
#                self._hdl_model_fitting_status_changed
#            ),
#            self._model.bn_analyses.on_changed.connect(
#                self._hdl_model_analyses_changed
#            )
#        ])
#
#        self._hdl_model_fitting_status_changed()
#        self._hdl_model_analyses_changed()
#
#    def _hdl_model_analyses_changed(self) -> None:
#        analyses = self._model.bn_analyses.get()
#
#        if len(analyses) == 1:
#            self.view.hide_graphs()
#        else:
#            self.view.show_graphs()
#
#    def _hdl_model_fitting_status_changed(self) -> None:
#        fitting_status = self._model.bn_fitting_status.get()
#
#        if fitting_status is IFTResultsModel.Status.FITTING:
#            footer_status = ResultsFooterStatus.IN_PROGRESS
#        elif fitting_status is IFTResultsModel.Status.FINISHED:
#            footer_status = ResultsFooterStatus.FINISHED
#            self.view.hide_confirm_cancel_dialog()
#        elif fitting_status is IFTResultsModel.Status.CANCELLED:
#            footer_status = ResultsFooterStatus.CANCELLED
#            self.view.hide_confirm_cancel_dialog()
#        else:
#            footer_status = ResultsFooterStatus.IN_PROGRESS
#
#        self.bn_footer_status.set(footer_status)
#
#    _update_times_handle = None
#
#    def _update_times(self) -> None:
#        if self._update_times_handle is not None:
#            self._update_times_handle.cancel()
#            self._update_times_handle = None
#
#        time_elapsed = self._model.calculate_time_elapsed()
#        self.bn_time_elapsed.set(time_elapsed)
#
#        time_remaining = self._model.calculate_time_remaining()
#        self.bn_time_remaining.set(time_remaining)
#
#        fitting_status = self._model.bn_fitting_status.get()
#
#        if fitting_status is IFTResultsModel.Status.FITTING:
#            self._update_times_handle = self._loop.call_later(
#                delay=self.UPDATE_TIME_INTERVAL,
#                callback=self._update_times,
#            )
#
#    def back(self) -> None:
#        if self._model.is_safe_to_discard:
#            self._back()
#        else:
#            self.view.show_confirm_discard_dialog()
#
#    def hdl_confirm_discard_response(self, accept: bool) -> None:
#        if accept:
#            self._back()
#
#        self.view.hide_confirm_discard_dialog()
#
#    def _back(self) -> None:
#        self._page_controls.prev_page()
#
#    def cancel(self) -> None:
#        if self._model.is_safe_to_discard:
#            self._cancel()
#        else:
#            self.view.show_confirm_cancel_dialog()
#
#    def hdl_confirm_cancel_response(self, accept: bool) -> None:
#        if accept:
#            self._cancel()
#
#        self.view.hide_confirm_cancel_dialog()
#
#    def _cancel(self):
#        self._model.cancel_analyses()
#
#    def save(self) -> None:
#        if self._active_save_options is not None:
#            return
#
#        self._active_save_options = self._model.create_save_options()
#        self.view.show_save_dialog(self._active_save_options)
#
#    def hdl_save_dialog_response(self, should_save: bool) -> None:
#        if self._active_save_options is None:
#            return
#
#        self.view.hide_save_dialog()
#
#        save_options = self._active_save_options
#        self._active_save_options = None
#
#        if should_save:
#            self._model.save_analyses(save_options)
#
#    def _do_destroy(self) -> None:
#        for ec in self.__event_connections:
#            ec.disconnect()
#
#        if self._update_times_handle is not None:
#            self._update_times_handle.cancel()
