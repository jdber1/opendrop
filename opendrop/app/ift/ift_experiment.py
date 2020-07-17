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
from gi.repository import Gtk

from injector import inject

from opendrop.app.common.image_acquisition import image_acquisition_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.footer.results import results_footer_cs, ResultsFooterStatus
from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import ComponentFactory, Presenter, TemplateChild, component
from opendrop.utility.bindable import VariableBindable
from opendrop.widgets.yes_no_dialog import YesNoDialog

from .services.session import IFTSession, IFTSessionModule
from .analysis_saver import ift_save_dialog_cs


@component(
    template_path='./ift_experiment.ui',
    modules=[IFTSessionModule],
)
class IFTExperimentPresenter(Presenter[Gtk.Assistant]):
    footer_area = TemplateChild('action_area')  # type: TemplateChild[Gtk.Stack]
    footer0 = TemplateChild('action0')  # type: TemplateChild[Gtk.Container]
    footer1 = TemplateChild('action1')  # type: TemplateChild[Gtk.Container]
    footer2 = TemplateChild('action2')  # type: TemplateChild[Gtk.Container]
    footer3 = TemplateChild('action3')  # type: TemplateChild[Gtk.Container]

    @inject
    def __init__(self, cf: ComponentFactory, session: IFTSession) -> None:
        self.cf = cf
        self.session = session

    def after_view_init(self) -> None:
        session = self.session
        session.bn_analyses.on_changed.connect(self.hdl_session_analyses_changed)

        self.analyses_event_connections = ()

        # Footer
        self._lin_footer_component = linear_navigator_footer_cs.factory(
            do_back=self.previous_page,
            do_next=self.next_page,
        ).create()
        self._lin_footer_component.view_rep.show()
        self.footer0.add(self._lin_footer_component.view_rep)

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
            do_cancel=self.request_cancel_analyses,
            do_save=self.request_save_analyses,
        ).create()
        self._results_footer_component.view_rep.show()
        self.footer3.add(self._results_footer_component.view_rep)

        # Image acquisition.
        self.image_acquisition_component = image_acquisition_cs.factory(
            model=session.image_acquisition,
            footer_area=Gtk.Grid(),  # ignore footer area for now
            page_controls=WizardPageControls(do_next_page=lambda: None, do_prev_page=lambda: None),
        ).create()
        self.image_acquisition_component.view_rep.show()

        # Physical parameters.
        self._physical_parameters_page = self.cf.create('IFTPhysicalParametersForm')
        self._physical_parameters_page.show()

        # Image processing.
        self._ift_image_processing_page = self.cf.create('IFTImageProcessing')
        self._ift_image_processing_page.show()

        # Report.
        self._report_page = self.cf.create('IFTReport')
        self._report_page.show()

        # Add pages to Assistant.
        self.host.append_page(self.image_acquisition_component.view_rep)
        self.host.child_set(
            self.image_acquisition_component.view_rep,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image acquisition',
        )

        self.host.append_page(self._physical_parameters_page)
        self.host.child_set(self._physical_parameters_page,
            title='Physical parameters',
            page_type=Gtk.AssistantPageType.CUSTOM,
            complete=True,
        )

        self.host.append_page(self._ift_image_processing_page)
        self.host.child_set(
            self._ift_image_processing_page,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image processing',
        )

        self.host.append_page(self._report_page)
        self.host.child_set(
            self._report_page,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Results',
        )

        self.host.set_current_page(0)

    def hdl_session_analyses_changed(self):
        analyses = self.session.bn_analyses.get()
        for conn in self.analyses_event_connections:
            conn.disconnect()

        self.analyses_event_connections = []
        for analysis in analyses:
            self.analyses_event_connections += (
                analysis.bn_status.on_changed.connect(self.hdl_session_analyses_status_changed),
                analysis.bn_time_start.on_changed.connect(self.hdl_session_analyses_time_start_changed),
                analysis.bn_time_est_complete.on_changed.connect(self.hdl_session_analyses_time_est_complete_changed),
            )

        self.hdl_session_analyses_status_changed()
        self.hdl_session_analyses_time_start_changed()
        self.hdl_session_analyses_time_est_complete_changed()

    def hdl_session_analyses_status_changed(self) -> None:
        analyses = self.session.bn_analyses.get()
        if not analyses:
            return

        is_done = all(a.bn_is_done.get() for a in analyses)
        is_cancelled = any(a.bn_is_cancelled.get() for a in analyses)

        if is_done:
            if self.cancel_dialog is not None:
                cancel_dialog = self.cancel_dialog
                self.cancel_dialog = None
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

    def hdl_session_analyses_time_start_changed(self) -> None:
        self.update_times()

    def hdl_session_analyses_time_est_complete_changed(self) -> None:
        self.update_times()

    def update_times(self) -> None:
        analyses = self.session.bn_analyses.get()
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
        cur_page = self.host.get_current_page()
        if cur_page in (0, 1):
            self.host.next_page()
        elif cur_page == 2:
            self.start_analyses()
            self.host.next_page()
        else:
            # Ignore, on last page.
            return

    def previous_page(self) -> None:
        cur_page = self.host.get_current_page()
        if cur_page == 0:
            # Ignore, on first page.
            return
        elif cur_page in (1, 2):
            self.host.previous_page()
        elif cur_page == 3:
            self.clear_analyses()
            self.host.previous_page()

    cancel_dialog = None
    def request_cancel_analyses(self) -> None:
        if self.cancel_dialog is not None:
            return

        self.cancel_dialog = YesNoDialog(
            parent=self.host,
            message_format='Confirm cancel analysis?',
        )

        self.cancel_dialog.connect('response', self.hdl_cancel_dialog_response)
        self.cancel_dialog.show()

    def hdl_cancel_dialog_response(self, dialog: Gtk.Widget, response: Gtk.ResponseType) -> None:
        self.cancel_dialog = None
        dialog.destroy()
        if (response == Gtk.ResponseType.YES):
            self.cancel_analyses()

    def start_analyses(self) -> None:
        self.session.start_analyses()

    def cancel_analyses(self) -> None:
        self.session.cancel_analyses()

    def clear_analyses(self) -> None:
        self.session.clear_analyses()

    save_dialog_component = None
    save_options = None
    def request_save_analyses(self) -> None:
        if self.save_dialog_component is not None:
            return

        if self.save_options is None:
            self.save_options = self.session.create_save_options()

        self.save_dialog_component = ift_save_dialog_cs.factory(
            parent_window=self.host,
            model=self.save_options,
            do_ok=self.hdl_save_dialog_ok,
            do_cancel=self.hdl_save_dialog_cancel,
        ).create()
        self.save_dialog_component.view_rep.show()

    def hdl_save_dialog_ok(self) -> None:
        if self.save_dialog_component is None:
            return

        save_dialog_component = self.save_dialog_component
        self.save_dialog_component = None
        save_dialog_component.destroy()

        if self.save_options is None:
            return

        save_options = self.save_options
        self.save_options = None

        self.session.save_analyses(save_options)

    def hdl_save_dialog_cancel(self) -> None:
        if self.save_dialog_component is None:
            return

        save_dialog_component = self.save_dialog_component
        self.save_dialog_component = None
        save_dialog_component.destroy()

        self.save_options = None

    def prepare(self, *_) -> None:
        # Update footer to show current page's action widgets.
        cur_page = self.host.get_current_page()
        if cur_page in (0, 1, 2):
            self.footer_area.set_visible_child_name('0')
        else:
            self.footer_area.set_visible_child_name(str(cur_page))

    def delete_event(self, *_) -> bool:
        self.request_close()
        return True

    def request_close(self, discard_unsaved: bool = False) -> None:
        if discard_unsaved:
            self.session.finish()
            self.host.destroy()
            return

        if not self.session.check_if_safe_to_discard_analyses():
            self.show_confirm_discard_dialog()
            return

        self.session.finish()
        self.host.destroy()

    confirm_discard_dialog = None
    def show_confirm_discard_dialog(self) -> None:
        if self.confirm_discard_dialog is not None:
            return

        self.confirm_discard_dialog = YesNoDialog(
            message_format='Discard unsaved results?',
            parent=self.host,
        )

        self.confirm_discard_dialog.connect('response', self.hdl_confirm_discard_dialog_response)
        self.confirm_discard_dialog.show()

    def hdl_confirm_discard_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        discard = (response == Gtk.ResponseType.YES)
        if discard:
            self.request_close(True)
        self.confirm_discard_dialog = None
        widget.destroy()

    def destroy(self, *_) -> None:
        self.image_acquisition_component.destroy()
        self._lin_footer_component.destroy()
        self._results_footer_component.destroy()

        for conn in self.analyses_event_connections:
            conn.disconnect()
