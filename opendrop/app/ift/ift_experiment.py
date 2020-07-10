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


from gi.repository import Gdk, Gtk

from opendrop.app.common.image_acquisition import image_acquisition_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.appfw import Inject, Injector, TemplateChild, componentclass
from opendrop.widgets.yes_no_dialog import YesNoDialog

from .image_processing import IFTImageProcessing
from .services.session import IFTSession
from .physical_parameters import IFTPhysicalParametersForm
from .results import ift_results_cs


@componentclass(
    template_path='./ift_experiment.ui',
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

        # Footer
        self._lin_footer_component = linear_navigator_footer_cs.factory(
            do_back=self.previous_page,
            do_next=self.next_page,
        ).create()
        self._lin_footer_component.view_rep.show()
        self._footer0.add(self._lin_footer_component.view_rep)

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

        # Results.
        self._ift_results_component = ift_results_cs.factory(
            model=session.results,
            footer_area=self._footer3,
            page_controls=WizardPageControls(do_next_page=self.next_page, do_prev_page=self.previous_page),
        ).create()
        self._ift_results_component.view_rep.show()

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

        self.append_page(self._ift_results_component.view_rep)
        self.child_set(
            self._ift_results_component.view_rep,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Results',
        )

        self.set_current_page(0)

    def next_page(self) -> None:
        cur_page = self.get_current_page()
        if cur_page in (0, 1):
            super().next_page()
        elif cur_page == 2:
            self._session.start_analyses()
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
            self._session.clear_analyses()
            super().previous_page()

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

        self._confirm_discard_dialog.connect('response', self._hdl_confirm_cancel_dialog_response)
        self._confirm_discard_dialog.show()

    def _hdl_confirm_cancel_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        discard = (response == Gtk.ResponseType.YES)
        if discard:
            self._request_close(True)
        self._confirm_discard_dialog = None
        widget.destroy()

    def do_destroy(self) -> None:
        self._image_acquisition_component.destroy()
        self._ift_results_component.destroy()
        self._lin_footer_component.destroy()

        Gtk.Widget.do_destroy.invoke(Gtk.Assistant, self)
