import asyncio
from typing import Any, Callable, MutableSequence, Sequence

from gi.repository import Gtk

from opendrop.app.common.analysis_model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.page.image_acquisition import ImageAcquisitionSpeaker
from opendrop.app.common.validation.image_acquisition.default_types_validator import create_subvalidator_for_impl
from opendrop.app.common.validation.image_acquisition.validator import ImageAcquisitionValidator
from opendrop.app.ift.analysis_model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory
from opendrop.app.ift.footer import FooterNavigatorView, FooterNavigatorPresenter
from opendrop.app.ift.page.image_processing import IFTImageProcessingSpeaker
from opendrop.app.ift.page.phys_params import IFTPhysicalParametersSpeaker
from opendrop.app.ift.validation.phys_params_validator import IFTPhysicalParametersFactoryValidator
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.component.wizard.sidebar import SidebarWizardPositionView
from opendrop.component.wizard.wizard import WizardPageID, WizardPositionPresenter
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
        self.footer_view = FooterNavigatorView()
        self.widget.attach(self.footer_view.widget, 0, 2, 2, 1)

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

        # Physical parameters
        phys_params_factory = IFTPhysicalParametersFactory()

        # Image annotator
        image_annotator = IFTImageAnnotator()

        # Create validators
        image_acquisition_validator = ImageAcquisitionValidator(create_subvalidator_for_impl, image_acquisition)
        phys_params_factory_validator = IFTPhysicalParametersFactoryValidator(phys_params_factory)

        # Create the wizard
        self._wizard_mod = Moderator()
        self._wizard_content_model = StackModel()
        page_order = self._create_wizard_pages(self._wizard_mod, self._wizard_content_model, image_acquisition,
                                               phys_params_factory, image_annotator)

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

        # FooterNavigatorPresenter
        footer_presenter = FooterNavigatorPresenter(
            wizard_mod=self._wizard_mod,
            page_order=page_order,
            validators={
                IFTWizardPageID.IMAGE_ACQUISITION: image_acquisition_validator,
                IFTWizardPageID.PHYS_PARAMS: phys_params_factory_validator},
            view=self._root_view.footer_view)
        self._cleanup_tasks.append(footer_presenter.destroy)

        # Make root view visible.
        self._root_view_parent_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self):
        for f in self._cleanup_tasks:
            f()

        self._cleanup_tasks = []

    @staticmethod
    def _create_wizard_pages(wizard_mod: Moderator, wizard_content_model: StackModel,
                             image_acquisition: ImageAcquisition, phys_params_factory: IFTPhysicalParametersFactory,
                             image_annotator: IFTImageAnnotator) \
            -> Sequence[IFTWizardPageID]:
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
            IFTPhysicalParametersSpeaker(phys_params_factory, wizard_content_model)
        )
        page_order.append(IFTWizardPageID.PHYS_PARAMS)

        # Image processing
        wizard_mod.add_speaker(
            IFTWizardPageID.IMAGE_PROCESSING,
            IFTImageProcessingSpeaker(image_annotator, image_acquisition.create_preview, wizard_content_model)
        )
        page_order.append(IFTWizardPageID.IMAGE_PROCESSING)

        return page_order
