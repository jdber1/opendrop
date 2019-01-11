import asyncio
import functools
from typing import Any, Callable, MutableSequence, Sequence, TypeVar, Type, Union

from gi.repository import Gtk

from opendrop.app.common.analysis_model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.forms import Form
from opendrop.app.common.forms.image_acquisition import ImageAcquisitionForm
from opendrop.app.common.page.extra import ActivePageIndicatorSidebarPresenter
from opendrop.app.common.page.page import Page
from opendrop.app.common.sidebar import WizardSidebarView
from opendrop.app.ift.analysis_model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory
from opendrop.app.common.footer import LinearNavigatorFooter
from opendrop.app.ift.forms.image_processing import IFTImageProcessingForm
from opendrop.app.ift.forms.phys_params import IFTPhysicalParametersForm
from opendrop.app.ift.forms.results import IFTResultsPageContent
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.component.wizard.wizard import WizardPageID
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.speaker import Speaker
from opendrop.utility.switch import Switch, RadioSwitchCoordinator

T = TypeVar('T')
U = TypeVar('U')


def _try_except(func: Callable[..., T], exc: Type[Exception], default: U) -> Callable[..., Union[T, U]]:
    def wrapper(*args, **kwargs) -> Union[T, U]:
        try:
            return func(*args, **kwargs)
        except exc:
            return default

    return wrapper


class IFTWizardPageID(WizardPageID):
    IMAGE_ACQUISITION = ('Image acquisition',)
    PHYS_PARAMS = ('Physical parameters',)
    IMAGE_PROCESSING = ('Image processing',)
    RESULTS = ('Results',)


class IFTRootView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        # Sidebar
        self.sidebar_view = WizardSidebarView()
        self.widget.attach(self.sidebar_view.widget, 0, 0, 1, 1)

        # Main content area
        self.content_stack_view = StackView()
        self.widget.attach(self.content_stack_view.widget, 1, 0, 1, 1)

        # Footer separator
        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 2, 1)

        # Footer
        self.footer_stack_view = StackView()
        self.widget.attach(self.footer_stack_view.widget, 0, 2, 2, 1)

        self.widget.show_all()


class PagesPresenter:
    def __init__(self, pages: Sequence[Page], content_stack_view: StackView, footer_stack_view: StackView) -> None:
        self._pages = pages
        self._content_stack_view = content_stack_view
        self._footer_stack_view = footer_stack_view

        self._content_stack_model = StackModel()
        self._footer_stack_model = StackModel()

        for page in self._pages:
            self._content_stack_model.add_child(page, page.content_view)
            self._footer_stack_model.add_child(page, page.footer_view)
            page.control_switch.on_turned_on.connect(functools.partial(self._hdl_page_turned_on, page),
                                                     strong_ref=True, immediate=True)
            if page.control_switch.is_on:
                self._hdl_page_turned_on(page)

        self._content_stack_presenter = StackPresenter(self._content_stack_model, self._content_stack_view)
        self._footer_stack_presenter = StackPresenter(self._footer_stack_model, self._footer_stack_view)

    def _hdl_page_turned_on(self, page: Page) -> None:
        self._content_stack_model.visible_child_key = page
        self._footer_stack_model.visible_child_key = page

    def destroy(self) -> None:
        self._content_stack_presenter.destroy()
        self._footer_stack_presenter.destroy()


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
        image_annotator = IFTImageAnnotator(image_acquisition.get_image_size_hint)

        phys_params_image_annotator_needle_width_binding = \
            Binding(phys_params_factory.bn_needle_width, image_annotator.bn_needle_width)
        self._cleanup_tasks.append(phys_params_image_annotator_needle_width_binding.unbind)

        # Create the wizard pages
        pages = self._create_wizard_pages(image_acquisition, phys_params_factory, image_annotator)

        # Manage each page's control switch so that only one can be 'on' at a time.
        RadioSwitchCoordinator([page.control_switch for page in pages])

        # Activate the first page
        pages[0].control_switch.on()

        # Create core UI presenters
        pages_presenter = PagesPresenter(pages, self._root_view.content_stack_view, self._root_view.footer_stack_view)
        self._cleanup_tasks.append(pages_presenter.destroy)

        # Sidebar
        sidebar_presenter = ActivePageIndicatorSidebarPresenter(pages, self._root_view.sidebar_view)
        self._cleanup_tasks.append(sidebar_presenter.destroy)

        # Make root view visible.
        self._root_view_parent_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self):
        for f in self._cleanup_tasks:
            f()

        self._cleanup_tasks = []

    @staticmethod
    def _create_wizard_pages(image_acquisition: ImageAcquisition, phys_params_factory: IFTPhysicalParametersFactory,
                             image_annotator: IFTImageAnnotator) \
            -> Sequence[Page]:
        # Page control switches
        image_acquisition_page_switch = Switch()
        phys_params_page_switch = Switch()
        image_processing_page_switch = Switch()
        results_page_switch = Switch()

        # Page contents
        image_acquisition_form = ImageAcquisitionForm(image_acquisition)
        phys_params_form = IFTPhysicalParametersForm(phys_params_factory)
        image_processing_form = IFTImageProcessingForm(
            image_annotator, _try_except(image_acquisition.create_preview, exc=ValueError, default=None))
        results_page_content = IFTResultsPageContent()

        class ValidateFormThenDoThis:
            def __init__(self, form: Form, then: Callable) -> None:
                self._form = form
                self._then = then

            def __call__(self) -> None:
                if self._form.validate():
                    self._then()

        # Page footers
        image_acquisition_footer = LinearNavigatorFooter(
            next=ValidateFormThenDoThis(image_acquisition_form, then=phys_params_page_switch.on))
        phys_params_footer = LinearNavigatorFooter(
            next=ValidateFormThenDoThis(phys_params_form, then=image_processing_page_switch.on),
            back=image_acquisition_page_switch.on)
        image_processing_footer = LinearNavigatorFooter(
            next=ValidateFormThenDoThis(image_processing_form, then=results_page_switch.on),
            back=phys_params_page_switch.on)
        results_page_footer = LinearNavigatorFooter(
            back=image_processing_page_switch.on
        )

        pages = [
            Page(
                name='Image acquisition',
                control_switch=image_acquisition_page_switch,
                content=image_acquisition_form,
                footer=image_acquisition_footer),
            Page(
                name='Physical parameters',
                control_switch=phys_params_page_switch,
                content=phys_params_form,
                footer=phys_params_footer),
            Page(
                name='Image processing',
                control_switch=image_processing_page_switch,
                content=image_processing_form,
                footer=image_processing_footer),
            Page(
                name='Results',
                control_switch=results_page_switch,
                content=results_page_content,
                footer=results_page_footer)]

        return pages
