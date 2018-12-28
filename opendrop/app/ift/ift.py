import asyncio
from typing import Any, Callable, MutableSequence, Sequence

from gi.repository import Gtk

from opendrop.app.common.analysis_model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.page.image_acquisition import ImageAcquisitionSpeaker
from opendrop.app.common.sidebar_wizard_pos_view import SidebarWizardPositionView
from opendrop.app.common.wizard import WizardPageID, WizardPositionPresenter
from opendrop.app.ift.footer import FooterView
from opendrop.app.ift.page.phys_params import PhysicalParametersSpeaker
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.utility.speaker import Speaker, Moderator


class IFTWizardPageID(WizardPageID):
    IMAGE_ACQUISITION = ('Image acquisition',)
    PHYS_PARAMS = ('Physical parameters',)
    IMAGE_PROCESSING = ('Image processing',)
    RESULTS = ('Results',)


class IFTRootView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        # Sidebar
        self.wizard_position_view = SidebarWizardPositionView()
        self.widget.attach(self.wizard_position_view.widget, 0, 0, 1, 1)

        # Main content area
        self.content_stack_view = StackView()
        self.widget.attach(self.content_stack_view.widget, 1, 0, 1, 1)

        # Footer separator
        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 2, 1)

        # Footer
        self.footer = FooterView()
        self.widget.attach(self.footer.widget, 0, 2, 2, 1)

        self.widget.show_all()


class IFTSpeaker(Speaker):
    def __init__(self, parent_content_stack: StackModel) -> None:
        super().__init__()

        self._loop = asyncio.get_event_loop()
        self._cleanup_tasks = []  # type: MutableSequence[Callable[[], Any]]

        self._root_view = IFTRootView()
        self._root_view_stack_key = object()
        self._root_view_parent_stack = parent_content_stack
        self._root_view_parent_stack.add_child(self._root_view_stack_key, self._root_view)

    def do_activate(self):
        self._loop.create_task(self._do_activate())

    async def _do_activate(self):
        # Create the analysis models
        # Image acquisition
        image_acquisition = ImageAcquisition()
        self._cleanup_tasks.append(image_acquisition.destroy)
        # Set the default image acquisition implementation to be 'local images'
        image_acquisition.type = DefaultImageAcquisitionImplType.LOCAL_IMAGES

        # Create the wizard
        self._wizard_mod = Moderator()
        self._wizard_content_model = StackModel()
        page_order = self._create_wizard_pages(self._wizard_mod, self._wizard_content_model, image_acquisition)

        # Activate the first page of the wizard
        await self._wizard_mod.activate_speaker_by_key(page_order[0])
        self._cleanup_tasks.append(lambda: self._loop.create_task(self._wizard_mod.activate_speaker_by_key(None)))

        # Create core UI presenters
        # WizardPositionPresenter
        wiz_pos_presenter = WizardPositionPresenter(self._wizard_mod, page_order, self._root_view.wizard_position_view)
        self._cleanup_tasks.append(wiz_pos_presenter.destroy)

        # StackPresenter
        content_stack_presenter = StackPresenter(self._wizard_content_model, self._root_view.content_stack_view)
        self._cleanup_tasks.append(content_stack_presenter.destroy)

        # Make root view visible.
        self._root_view_parent_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self):
        for f in self._cleanup_tasks:
            f()

        self._cleanup_tasks = []

    @staticmethod
    def _create_wizard_pages(wizard_mod: Moderator, wizard_content_model: StackModel,
                             image_acquisition: ImageAcquisition) -> Sequence[IFTWizardPageID]:
        page_order = []  # type: MutableSequence[IFTWizardPageID]

        # Image acquisition speaker
        wizard_mod.add_speaker(
            IFTWizardPageID.IMAGE_ACQUISITION,
            ImageAcquisitionSpeaker(image_acquisition, wizard_content_model)
        )
        page_order.append(IFTWizardPageID.IMAGE_ACQUISITION)

        # Physical parameters
        wizard_mod.add_speaker(
            IFTWizardPageID.PHYS_PARAMS,
            PhysicalParametersSpeaker()
        )
        page_order.append(IFTWizardPageID.PHYS_PARAMS)

        return page_order
