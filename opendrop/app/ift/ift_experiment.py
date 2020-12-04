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


from gi.repository import GObject, Gtk
from injector import inject

from opendrop.app.common.footer.analysis import AnalysisFooterStatus
from opendrop.appfw import Presenter, TemplateChild, component
from opendrop.widgets.yes_no_dialog import YesNoDialog

from .analysis_saver import ift_save_dialog_cs
from .services.progress import IFTAnalysisProgressHelper
from .services.session import IFTSession, IFTSessionModule


@component(
    template_path='./ift_experiment.ui',
    modules=[IFTSessionModule],
)
class IFTExperimentPresenter(Presenter[Gtk.Assistant]):
    action_area = TemplateChild('action_area')  # type: TemplateChild[Gtk.Stack]
    analysis_footer = TemplateChild('analysis_footer')

    report_page = TemplateChild('report_page')

    @inject
    def __init__(self, session: IFTSession, progress_helper: IFTAnalysisProgressHelper) -> None:
        self.session = session
        self.progress_helper = progress_helper

        session.bind_property('analyses', self.progress_helper, 'analyses', GObject.BindingFlags.SYNC_CREATE)

    def after_view_init(self) -> None:
        self.session.bind_property('analyses', self.report_page, 'analyses', GObject.BindingFlags.SYNC_CREATE)

        self.progress_helper.bind_property(
            'status', self.analysis_footer, 'status', GObject.BindingFlags.SYNC_CREATE,
            lambda binding, x: {
                IFTAnalysisProgressHelper.Status.ANALYSING: AnalysisFooterStatus.IN_PROGRESS,
                IFTAnalysisProgressHelper.Status.FINISHED: AnalysisFooterStatus.FINISHED,
                IFTAnalysisProgressHelper.Status.CANCELLED: AnalysisFooterStatus.CANCELLED,
            }[x],
            None,
        )

        self.progress_helper.bind_property(
            'fraction', self.analysis_footer, 'progress', GObject.BindingFlags.SYNC_CREATE
        )
        self.progress_helper.bind_property(
            'time-start', self.analysis_footer, 'time-start', GObject.BindingFlags.SYNC_CREATE
        )
        self.progress_helper.bind_property(
            'est-complete', self.analysis_footer, 'time-complete', GObject.BindingFlags.SYNC_CREATE
        )

    def prepare(self, *_) -> None:
        # Update footer to show current page's action widgets.
        cur_page = self.host.get_current_page()
        self.action_area.set_visible_child_name(str(cur_page))

    def next_page(self, *_) -> None:
        cur_page = self.host.get_current_page()
        if cur_page == 0:
            self.host.next_page()
        elif cur_page == 1:
            self.start_analyses()
            self.host.next_page()
        else:
            # Ignore, on last page.
            return

    def previous_page(self, *_) -> None:
        cur_page = self.host.get_current_page()
        if cur_page == 0:
            # Ignore, on first page.
            return
        elif cur_page == 1:
            self.host.previous_page()
        elif cur_page == 2:
            self.clear_analyses()
            self.host.previous_page()

    def start_analyses(self) -> None:
        self.session.start_analyses()

    def clear_analyses(self) -> None:
        self.session.clear_analyses()

    def cancel_analyses(self, *_) -> None:
        if hasattr(self, 'cancel_dialog'): return

        self.cancel_dialog = YesNoDialog(
            parent=self.host,
            message_format='Confirm stop analysis?',
        )

        def hdl_response(dialog: Gtk.Widget, response: Gtk.ResponseType) -> None:
            del self.cancel_dialog
            dialog.destroy()

            self.progress_helper.disconnect(status_handler_id)

            if response == Gtk.ResponseType.YES:
                self.session.cancel_analyses()

        def hdl_progress_status(*_) -> None:
            if (self.progress_helper.status is IFTAnalysisProgressHelper.Status.FINISHED or
                    self.progress_helper.status is IFTAnalysisProgressHelper.Status.CANCELLED):
                self.cancel_dialog.close()

        # Close dialog if analysis finishes or cancels before user responds.
        status_handler_id = self.progress_helper.connect('notify::status', hdl_progress_status)

        self.cancel_dialog.connect('response', hdl_response)

        self.cancel_dialog.show()

    def save_analyses(self, *_) -> None:
        if hasattr(self, 'save_dialog_component'): return

        save_options = self.session.create_save_options()

        def hdl_ok() -> None:
            self.save_dialog_component.destroy()
            del self.save_dialog_component
            self.session.save_analyses(save_options)

        def hdl_cancel() -> None:
            self.save_dialog_component.destroy()
            del self.save_dialog_component

        self.save_dialog_component = ift_save_dialog_cs.factory(
            parent_window=self.host,
            model=save_options,
            do_ok=hdl_ok,
            do_cancel=hdl_cancel,
        ).create()
        self.save_dialog_component.view_rep.show()

    def close(self, discard_unsaved: bool = False) -> None:
        if hasattr(self, 'confirm_discard_dialog'): return

        if discard_unsaved or self.session.safe_to_discard():
            self.session.quit()
            self.host.destroy()
        else:
            self.confirm_discard_dialog = YesNoDialog(
                message_format='Discard unsaved results?',
                parent=self.host,
            )

            def hdl_response(dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
                del self.confirm_discard_dialog
                dialog.destroy()

                if response == Gtk.ResponseType.YES:
                    self.close(True)

            self.confirm_discard_dialog.connect('response', hdl_response)
            self.confirm_discard_dialog.show()

    def delete_event(self, *_) -> bool:
        self.close()
        return True
