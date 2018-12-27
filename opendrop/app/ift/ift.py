import asyncio
from typing import Any, Callable, MutableSequence

from gi.repository import Gtk

from opendrop.app.common.analysis_model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.page.image_acquisition import ImageAcquisitionSpeaker
from opendrop.app.common.sidebar_wizard_pos_view import SidebarWizardPositionView
from opendrop.app.common.wizard import WizardPageID, WizardPositionPresenter
from opendrop.app.ift.footer import FooterView
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

        self._image_acquisition = ImageAcquisition()
        # Set the default image acquisition implementation to be 'local images'
        self._image_acquisition.type = DefaultImageAcquisitionImplType.LOCAL_IMAGES

        self._parent_content_stack = parent_content_stack
        self._root_view = IFTRootView()
        self._root_view_cskey = object()
        self._parent_content_stack.add_child(self._root_view_cskey, self._root_view)

        self._wizard_mod = Moderator()
        self._wizard_content_stack = StackModel()
        self._wizard_pages = []  # type: MutableSequence[IFTWizardPageID]
        self._create_wizard_pages()

    def _create_wizard_pages(self) -> None:
        # Image acquisition speaker
        self._wizard_mod.add_speaker(
            IFTWizardPageID.IMAGE_ACQUISITION,
            ImageAcquisitionSpeaker(self._image_acquisition, self._wizard_content_stack)
        )
        self._wizard_pages.append(IFTWizardPageID.IMAGE_ACQUISITION)

    def do_activate(self):
        self._loop.create_task(self._do_activate())

    async def _do_activate(self):
        # WizardPositionPresenter
        wiz_pos_presenter = WizardPositionPresenter(self._wizard_mod, self._wizard_pages,
                                                    self._root_view.wizard_position_view)
        self._cleanup_tasks.append(wiz_pos_presenter.destroy)

        # StackPresenter
        content_stack_presenter = StackPresenter(self._wizard_content_stack, self._root_view.content_stack_view)
        self._cleanup_tasks.append(content_stack_presenter.destroy)

        # Activate the first page of the wizard
        await self._wizard_mod.activate_speaker_by_key(self._wizard_pages[0])

        # Make root view visible.
        self._parent_content_stack.visible_child_key = self._root_view_cskey

    def do_deactivate(self):
        # Set the active wizard page/speaker to None to deactivate the currently active speaker/page.
        self._loop.create_task(self._wizard_mod.activate_speaker_by_key(None))

        for f in self._cleanup_tasks:
            f()

        self._cleanup_tasks = []
