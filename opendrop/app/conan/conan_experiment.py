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
from injector import inject

from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.appfw import ComponentFactory, Presenter, TemplateChild, component
from opendrop.widgets.yes_no_dialog import YesNoDialog

from .image_processing import conan_image_processing_cs
from .results import conan_results_cs
from .services.session import ConanSession, ConanSessionModule


@component(
    template_path='./conan_experiment.ui',
    modules=[ConanSessionModule],
)
class ConanExperimentPresenter(Presenter[Gtk.Assistant]):
    action_area = TemplateChild('action_area')  # type: TemplateChild[Gtk.Stack]
    action0 = TemplateChild('action0')  # type: TemplateChild[Gtk.Container]
    action1 = TemplateChild('action1')  # type: TemplateChild[Gtk.Container]
    action2 = TemplateChild('action2')  # type: TemplateChild[Gtk.Container]

    @inject
    def __init__(self, cf: ComponentFactory, session: ConanSession) -> None:
        self.cf = cf
        self.session = session

    def after_view_init(self) -> None:
        # Footer
        self.lin_footer_component = linear_navigator_footer_cs.factory(
            do_back=self.previous_page,
            do_next=self.next_page,
        ).create()
        self.lin_footer_component.view_rep.show()
        self.action0.add(self.lin_footer_component.view_rep)

        image_acquisition_page = self.cf.create('ImageAcquisition', visible=True)

        self.image_processing_component = conan_image_processing_cs.factory(
            model=self.session.image_processing,
            footer_area=Gtk.Grid(),  # ignore footer area for now
            page_controls=WizardPageControls(
                do_next_page=lambda: None,
                do_prev_page=lambda: None,
            ),
        ).create()
        self.image_processing_component.view_rep.show()

        self.results_component = conan_results_cs.factory(
            model=self.session.results,
            footer_area=self.action2,
            page_controls=WizardPageControls(
                do_next_page=self.next_page,
                do_prev_page=self.previous_page,
            ),
        ).create()
        self.results_component.view_rep.show()

        self.host.append_page(image_acquisition_page)
        self.host.child_set(
            image_acquisition_page,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image acquisition',
        )

        self.host.append_page(self.image_processing_component.view_rep)
        self.host.child_set(
            self.image_processing_component.view_rep,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Image processing',
        )

        self.host.append_page(self.results_component.view_rep)
        self.host.child_set(
            self.results_component.view_rep,
            page_type=Gtk.AssistantPageType.CUSTOM,
            title='Results',
        )

        self.host.set_current_page(0)

    def prepare(self, *_) -> None:
        cur_page = self.host.get_current_page()
        if cur_page in (0, 1):
            self.action_area.set_visible_child_name('0')
        else:
            self.action_area.set_visible_child_name(str(cur_page))

    def next_page(self) -> None:
        cur_page = self.host.get_current_page()
        if cur_page == 0:
            self.host.next_page()
        elif cur_page == 1:
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
        elif cur_page == 1:
            self.host.previous_page()
        elif cur_page == 2:
            self.clear_analyses()
            self.host.previous_page()

    def start_analyses(self) -> None:
        self.session.start_analyses()

    def clear_analyses(self) -> None:
        self.session.clear_analyses()

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

            def hdl_response(self, dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
                del self.confirm_discard_dialog
                dialog.destroy()

                if response == Gtk.ResponseType.YES:
                    self.close(True)

            self.confirm_discard_dialog.connect('response', hdl_response)
            self.confirm_discard_dialog.show()

    def delete_event(self, *_) -> bool:
        self.close()
        return True

    def destroy(self, *_) -> None:
        self.image_processing_component.destroy()
        self.results_component.destroy()
