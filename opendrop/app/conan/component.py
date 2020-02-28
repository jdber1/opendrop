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


from collections import OrderedDict
from enum import Enum

from gi.repository import Gtk, Gdk

from opendrop.app.common.image_acquisition import image_acquisition_cs
from opendrop.app.common.wizard import wizard_cs, WizardModel
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.widgets.yes_no_dialog import YesNoDialog
from .image_processing import conan_image_processing_cs
from .model import ConanSession
from .results import conan_results_cs

conan_root_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@conan_root_cs.view()
class ConanRootView(View['ConanRootPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._window = Gtk.Window(
            title='Contact Angle',
            window_position=Gtk.WindowPosition.CENTER,
            width_request=800,
            height_request=600,
        )

        _, wizard_area = self.new_component(
            wizard_cs.factory(
                controller=self.presenter.wizard_controller,
                titles=OrderedDict([
                    (
                        PageID.IMAGE_ACQUISITION,
                        'Image acquisition',
                    ), (
                        PageID.IMAGE_PROCESSING,
                        'Image processing',
                    ), (
                        PageID.RESULTS,
                        'Results',
                    ),
                ]),
                pages={
                    PageID.IMAGE_ACQUISITION:
                        image_acquisition_cs.factory(
                            model=self.presenter.image_acquisition_model,
                        ),
                    PageID.IMAGE_PROCESSING:
                        conan_image_processing_cs.factory(
                            model=self.presenter.image_processing_model,
                        ),
                    PageID.RESULTS:
                        conan_results_cs.factory(
                            model=self.presenter.results_model,
                        ),
                }
            )
        )
        wizard_area.show()
        self._window.add(wizard_area)

        self._window.connect('delete-event', self._hdl_window_delete_event)

        self._confirm_discard_dialog = None

        return self._window

    def _hdl_window_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
        self.presenter.exit()
        return True

    def show_confirm_discard_dialog(self) -> None:
        if self._confirm_discard_dialog is not None:
            return

        self._confirm_discard_dialog = YesNoDialog(
            message_format='Discard unsaved results?',
            parent=self._window,
        )

        self._confirm_discard_dialog.connect('delete-event', lambda *_: True)
        self._confirm_discard_dialog.connect('response', self._hdl_confirm_discard_dialog_response)

        self._confirm_discard_dialog.show()

    def _hdl_confirm_discard_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        discard = (response == Gtk.ResponseType.YES)
        self.presenter.hdl_confirm_discard_dialog_response(discard)

    def hide_confirm_discard_dialog(self) -> None:
        if self._confirm_discard_dialog is None:
            return

        self._confirm_discard_dialog.destroy()
        self._confirm_discard_dialog = None

    def _do_destroy(self) -> None:
        self._window.destroy()


@conan_root_cs.presenter(options=['session'])
class ConanRootPresenter(Presenter['ConanRootView']):
    def _do_init(self, session: ConanSession) -> None:
        self._session = session

        self.image_acquisition_model = session.image_acquisition
        self.image_processing_model = session.image_processing
        self.results_model = session.results

        self.wizard_controller = WizardModel(
            pages=[
                PageID.IMAGE_ACQUISITION,
                PageID.IMAGE_PROCESSING,
                PageID.RESULTS,
            ]
        )

        self.wizard_controller.register_interpage_action(
            start_page=PageID.IMAGE_PROCESSING,
            end_page=PageID.RESULTS,
            callback=self._start_analyses,
        )

        self.wizard_controller.register_interpage_action(
            start_page=PageID.RESULTS,
            end_page=PageID.IMAGE_PROCESSING,
            callback=self._clear_analyses,
        )

    def _start_analyses(self) -> None:
        self._session.start_analyses()

    def cancel_analyses(self) -> None:
        self._session.cancel_analyses()

    def _clear_analyses(self) -> None:
        self._session.clear_analyses()

    def exit(self, discard_unsaved: bool = False) -> None:
        if not self._session.check_if_safe_to_discard_analyses() and not discard_unsaved:
            self.view.show_confirm_discard_dialog()
            return

        self._session.exit()

    def hdl_confirm_discard_dialog_response(self, discard: bool) -> None:
        self.view.hide_confirm_discard_dialog()

        if discard:
            self.exit(discard_unsaved=discard)


class PageID(Enum):
    IMAGE_ACQUISITION = 0
    IMAGE_PROCESSING = 1
    RESULTS = 2
