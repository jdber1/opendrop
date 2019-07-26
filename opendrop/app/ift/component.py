from collections import OrderedDict
from enum import Enum

from gi.repository import Gtk, Gdk

from opendrop.app.common.image_acquisition import image_acquisition_cs
from opendrop.app.common.wizard import wizard_cs, WizardModel
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.widgets.yes_no_dialog import YesNoDialog
from .image_processing import ift_image_processing_cs
from .model import IFTSession
from .physical_parameters import physical_parameters_cs
from .results import ift_results_cs

ift_root_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@ift_root_cs.view()
class IFTRootView(View['IFTRootPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._window = Gtk.Window(
            title='Interfacial Tension',
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
                        PageID.PHYS_PARAMS,
                        'Physical parameters',
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
                    PageID.PHYS_PARAMS:
                        physical_parameters_cs.factory(
                            model=self.presenter.physical_parameters_model
                        ),
                    PageID.IMAGE_PROCESSING:
                        ift_image_processing_cs.factory(
                            model=self.presenter.image_processing_model,
                        ),
                    PageID.RESULTS:
                        ift_results_cs.factory(
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


@ift_root_cs.presenter(options=['session'])
class IFTRootPresenter(Presenter['IFTRootView']):
    def _do_init(self, session: IFTSession) -> None:
        self._session = session

        self.image_acquisition_model = session.image_acquisition
        self.physical_parameters_model = session.physical_parameters
        self.image_processing_model = session.image_processing
        self.results_model = session.results

        self.wizard_controller = WizardModel(
            pages=[
                PageID.IMAGE_ACQUISITION,
                PageID.PHYS_PARAMS,
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
    PHYS_PARAMS = 1
    IMAGE_PROCESSING = 2
    RESULTS = 3
