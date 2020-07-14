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


import time
from gi.repository import Gdk, Gtk

from opendrop.app.common.image_acquisition import image_acquisition_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.footer.results import results_footer_cs, ResultsFooterStatus
from opendrop.utility.bindable import VariableBindable
from opendrop.appfw import Inject, Injector, TemplateChild, componentclass
from opendrop.widgets.yes_no_dialog import YesNoDialog

from .image_processing import IFTImageProcessing
from .services.session import IFTSession, IFTSessionModule
from .physical_parameters import IFTPhysicalParametersForm
from .report import IFTReport
from .analysis import IFTDropAnalysis
from .analysis_saver import ift_save_dialog_cs


@componentclass(
    template_path='./ift_experiment.ui',
    modules=[IFTSessionModule],
)
class IFTExperiment(Gtk.Assistant):
    __gtype_name__ = 'IFTExperiment'

    _session = Inject(IFTSession)
    _injector = Inject(Injector)

    _footer_area = TemplateChild('action_area')
    _footer0 = TemplateChild('action0')
    _footer1 = TemplateChild('action1')
    _footer2 = TemplateChild('action2')
    _footer3 = TemplateChild('action3')

    def after_template_init(self):
        session = self._session
        session.bn_analyses.on_changed.connect(self._hdl_session_analyses_changed)

        self._analyses_event_connections = ()

        # Footer
        self._lin_footer_component = linear_navigator_footer_cs.factory(
            do_back=self.previous_page,
            do_next=self.next_page,
        ).create()
        self._lin_footer_component.view_rep.show()
        self._footer0.add(self._lin_footer_component.view_rep)

        self._results_footer_status = VariableBindable(ResultsFooterStatus.IN_PROGRESS)
        self._results_footer_progress = VariableBindable(0.0)
        self._results_footer_time_elapsed = VariableBindable(0.0)
        self._results_footer_time_remaining = VariableBindable(0.0)
        self._results_footer_component = results_footer_cs.factory(
            in_status=self._results_footer_status,
            in_progress=self._results_footer_progress,
            in_time_elapsed=self._results_footer_time_elapsed,
            in_time_remaining=self._results_footer_time_remaining,
            do_back=self.previous_page,
            do_cancel=self._request_cancel_analyses,
            do_save=self._request_save_analyses,
        ).create()
        self._results_footer_component.view_rep.show()
        self._footer3.add(self._results_footer_component.view_rep)

        # Image acquisition.
        self._image_acquisition_component = image_acquisition_cs.factory(
            model=session.image_acquisition,
            footer_area=Gtk.Grid(),  # ignore footer area for now
            page_controls=WizardPageControls(do_next_page=lambda: None, do_prev_page=lambda: None),
        ).create()
        self._image_acquisition_component.view_rep.show()

        # Physical parameters.
        self._physical_parameters_page = self._injector.create_object(IFTPhysicalParametersForm)
        self._physical_parameters_page.show()

        # Image processing.
        self._ift_image_processing_page = self._injector.create_object(IFTImageProcessing)
        self._ift_image_processing_page.show()

        # Report.
        self._report_page = self._injector.create_object(IFTReport)
        self._report_page.show()

        # Add pages to Assistant.
        self.append_page(self._image_acquisition_component.view_rep)
        self.child_set(
            self._image_acquisition_component.view_rep,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image acquisition',
        )

        self.append_page(self._physical_parameters_page)
        self.child_set(self._physical_parameters_page,
            title='Physical parameters',
            page_type=Gtk.AssistantPageType.CUSTOM,
            complete=True,
        )

        self.append_page(self._ift_image_processing_page)
        self.child_set(
            self._ift_image_processing_page,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image processing',
        )

        self.append_page(self._report_page)
        self.child_set(
            self._report_page,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Results',
        )

        self.set_current_page(0)

    def _hdl_session_analyses_changed(self):
        analyses = self._session.bn_analyses.get()
        for conn in self._analyses_event_connections:
            conn.disconnect()

        self._analyses_event_connections = []
        for analysis in analyses:
            self._analyses_event_connections += (
                analysis.bn_status.on_changed.connect(self._hdl_session_analyses_status_changed),
                analysis.bn_time_start.on_changed.connect(self._hdl_session_analyses_time_start_changed),
                analysis.bn_time_est_complete.on_changed.connect(self._hdl_session_analyses_time_est_complete_changed),
            )

        self._hdl_session_analyses_status_changed()
        self._hdl_session_analyses_time_start_changed()
        self._hdl_session_analyses_time_est_complete_changed()

    def _hdl_session_analyses_status_changed(self) -> None:
        analyses = self._session.bn_analyses.get()
        if not analyses:
            return

        is_done = all(a.bn_is_done.get() for a in analyses)
        is_cancelled = any(a.bn_is_cancelled.get() for a in analyses)

        if is_done:
            if self._cancel_dialog is not None:
                cancel_dialog = self._cancel_dialog
                self._cancel_dialog = None
                cancel_dialog.destroy()

            if is_cancelled:
                self._results_footer_status.set(ResultsFooterStatus.CANCELLED)
            else:
                self._results_footer_status.set(ResultsFooterStatus.FINISHED)
        else:
            self._results_footer_status.set(ResultsFooterStatus.IN_PROGRESS)

        num_analyses = len(analyses)
        num_finished = sum(a.bn_status.get() is IFTDropAnalysis.Status.FINISHED for a in analyses)
        progress = num_finished/num_analyses
        self._results_footer_progress.set(progress)

    def _hdl_session_analyses_time_start_changed(self) -> None:
        self._update_times()

    def _hdl_session_analyses_time_est_complete_changed(self) -> None:
        self._update_times()

    def _update_times(self) -> None:
        analyses = self._session.bn_analyses.get()
        if not analyses:
            return

        time_start = min(a.bn_time_start.get() for a in analyses)
        est_complete = min(a.bn_time_est_complete.get() for a in analyses)

        now = time.time()
        elapsed = now - time_start
        remaining = est_complete - now

        self._results_footer_time_remaining.set(remaining)
        self._results_footer_time_elapsed.set(elapsed)

    def next_page(self) -> None:
        cur_page = self.get_current_page()
        if cur_page in (0, 1):
            super().next_page()
        elif cur_page == 2:
            self._start_analyses()
            super().next_page()
        else:
            # Ignore, on last page.
            return

    def previous_page(self) -> None:
        cur_page = self.get_current_page()
        if cur_page == 0:
            # Ignore, on first page.
            return
        elif cur_page in (1, 2):
            super().previous_page()
        elif cur_page == 3:
            self._clear_analyses()
            super().previous_page()

    _cancel_dialog = None
    def _request_cancel_analyses(self) -> None:
        if self._cancel_dialog is not None:
            return

        self._cancel_dialog = YesNoDialog(
            parent=self,
            message_format='Confirm cancel analysis?',
        )

        self._cancel_dialog.connect('response', self._hdl_cancel_dialog_response)
        self._cancel_dialog.show()

    def _hdl_cancel_dialog_response(self, dialog: Gtk.Widget, response: Gtk.ResponseType) -> None:
        self._cancel_dialog = None
        dialog.destroy()
        if (response == Gtk.ResponseType.YES):
            self._cancel_analyses()

    # close dialog if finished

    def _start_analyses(self) -> None:
        self._session.start_analyses()

    def _cancel_analyses(self) -> None:
        self._session.cancel_analyses()

    def _clear_analyses(self) -> None:
        self._session.clear_analyses()

    _save_dialog_component = None
    _save_options = None
    def _request_save_analyses(self) -> None:
        if self._save_dialog_component is not None:
            return

        if self._save_options is None:
            self._save_options = self._session.create_save_options()

        self._save_dialog_component = ift_save_dialog_cs.factory(
            parent_window=self,
            model=self._save_options,
            do_ok=self._hdl_save_dialog_ok,
            do_cancel=self._hdl_save_dialog_cancel,
        ).create()
        self._save_dialog_component.view_rep.show()

    def _hdl_save_dialog_ok(self) -> None:
        if self._save_dialog_component is None:
            return

        save_dialog_component = self._save_dialog_component
        self._save_dialog_component = None
        save_dialog_component.destroy()

        if self._save_options is None:
            return

        save_options = self._save_options
        self._save_options = None

        self._session.save_analyses(save_options)

    def _hdl_save_dialog_cancel(self) -> None:
        if self._save_dialog_component is None:
            return

        save_dialog_component = self._save_dialog_component
        self._save_dialog_component = None
        save_dialog_component.destroy()

        self._save_options = None

    def do_prepare(self, page: Gtk.Widget) -> None:
        # Update footer to show current page's action widgets.
        cur_page = self.get_current_page()
        if cur_page in (0, 1, 2):
            self._footer_area.set_visible_child_name('0')
        else:
            self._footer_area.set_visible_child_name(str(self.get_current_page()))

    def do_delete_event(self, event: Gdk.EventAny) -> bool:
        self._request_close()
        return True

    def _request_close(self, discard_unsaved: bool = False) -> None:
        if discard_unsaved:
            self._session.finish()
            self.destroy()
            return

        if not self._session.check_if_safe_to_discard_analyses():
            self._show_confirm_discard_dialog()
            return

        self._session.finish()
        self.destroy()

    _confirm_discard_dialog = None
    def _show_confirm_discard_dialog(self) -> None:
        if self._confirm_discard_dialog is not None:
            return

        self._confirm_discard_dialog = YesNoDialog(
            message_format='Discard unsaved results?',
            parent=self,
        )

        self._confirm_discard_dialog.connect('response', self._hdl_confirm_discard_dialog_response)
        self._confirm_discard_dialog.show()

    def _hdl_confirm_discard_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        discard = (response == Gtk.ResponseType.YES)
        if discard:
            self._request_close(True)
        self._confirm_discard_dialog = None
        widget.destroy()

    def do_destroy(self) -> None:
        self._image_acquisition_component.destroy()
        self._lin_footer_component.destroy()
        self._results_footer_component.destroy()

        for conn in self._analyses_event_connections:
            conn.disconnect()

        Gtk.Widget.do_destroy.invoke(Gtk.Assistant, self)
