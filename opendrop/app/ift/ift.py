import asyncio
from operator import attrgetter
from typing import Any, Callable, MutableSequence, TypeVar, Type, Union, Optional

from gi.repository import Gtk

from opendrop.app.common.model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.content.image_acquisition import ImageAcquisitionFormPresenter, ImageAcquisitionFormView
from opendrop.app.common.footer import LinearNavigatorFooterView, LinearNavigatorFooterPresenter
from opendrop.app.common.sidebar import TasksSidebarPresenter, TasksSidebarView
from opendrop.app.ift.model.analyser import IFTAnalysis
from opendrop.app.ift.model.analysis_factory import IFTAnalysisFactory
from opendrop.app.ift.model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.model.phys_params import IFTPhysicalParametersFactory
from opendrop.app.ift.model.results_explorer import IFTResultsExplorer
from opendrop.app.ift.content.image_processing import IFTImageProcessingFormView, IFTImageProcessingFormPresenter
from opendrop.app.ift.content.phys_params import IFTPhysicalParametersFormPresenter, IFTPhysicalParametersFormView
from opendrop.app.ift.content.results import IFTResultsView, IFTResultsPresenter
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView
from opendrop.component.wizard.wizard import WizardPageID
from opendrop.mytypes import Rect2
from opendrop.utility.bindable.bindable import AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.events import EventConnection
from opendrop.utility.option import MutuallyExclusiveOptions
from opendrop.utility.speaker import Speaker

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

        # Page views
        self.content_image_acquisition = ImageAcquisitionFormView()
        self.footer_image_acquisition = LinearNavigatorFooterView()

        self.content_phys_params = IFTPhysicalParametersFormView()
        self.footer_phys_params = LinearNavigatorFooterView()

        self.content_image_processing = IFTImageProcessingFormView()
        self.footer_image_processing = LinearNavigatorFooterView()

        self.content_results = IFTResultsView()
        self.footer_results = LinearNavigatorFooterView()

        # Sidebar
        self.sidebar_view = TasksSidebarView(attrgetter('title'))  # type: TasksSidebarView[IFTWizardPageID]
        self.widget.attach(self.sidebar_view.widget, 0, 0, 1, 1)

        # Main content container
        self._content_view = StackView()
        self.widget.attach(self._content_view.widget, 1, 0, 1, 1)

        self._content_view.add_child(self.content_image_acquisition)
        self._content_view.add_child(self.content_phys_params)
        self._content_view.add_child(self.content_image_processing)
        self._content_view.add_child(self.content_results)

        # Main content and Footer separator
        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 2, 1)

        # Footer container
        self._footer_view = StackView()
        self.widget.attach(self._footer_view.widget, 0, 2, 2, 1)

        self._footer_view.add_child(self.footer_image_acquisition)
        self._footer_view.add_child(self.footer_phys_params)
        self._footer_view.add_child(self.footer_image_processing)
        self._footer_view.add_child(self.footer_results)

        self.widget.show_all()

    active_content_view = property()
    active_footer_view = property()

    @active_content_view.setter
    def active_content_view(self, view: GtkWidgetView) -> None:
        self._content_view.set_visible_child(view)

    @active_footer_view.setter
    def active_footer_view(self, view: GtkWidgetView) -> None:
        self._footer_view.set_visible_child(view)


class IfThen:
    def __init__(self, cond: Callable, then: Callable) -> None:
        self._cond = cond
        self._then = then

    def __call__(self) -> None:
        if self._cond():
            self._then()


class IfThenElse:
    def __init__(self, cond: Callable, then: Callable, else_: Callable) -> None:
        self._cond = cond
        self._then = then
        self._else = else_

    def __call__(self) -> None:
        if self._cond():
            self._then()
        else:
            self._else()


class IFTRootPresenter:
    def __init__(self, image_acquisition: ImageAcquisition, phys_params: IFTPhysicalParametersFactory,
                 image_annotator: IFTImageAnnotator, create_analysis: Callable[[], IFTAnalysis],
                 results_explorer: IFTResultsExplorer, view: IFTRootView):
        self._view = view
        self._create_analysis = create_analysis
        self._results_explorer = results_explorer

        self.__cleanup_tasks = []
        event_connections = []  # type: MutableSequence[EventConnection]

        self._page_option_image_acquisition = AtomicBindableVar(False)
        self._page_option_phys_params = AtomicBindableVar(False)
        self._page_option_image_processing = AtomicBindableVar(False)
        self._page_option_results = AtomicBindableVar(False)

        # Manage options so that only one can be set to True at a time.
        MutuallyExclusiveOptions((
            self._page_option_image_acquisition,
            self._page_option_phys_params,
            self._page_option_image_processing,
            self._page_option_results))

        # Main content
        # Image acquisition
        self._content_image_acquisition = ImageAcquisitionFormPresenter(
            image_acquisition=image_acquisition,
            view=self._view.content_image_acquisition)
        self.__cleanup_tasks.append(self._content_image_acquisition.destroy)

        # Physical parameters
        self._content_phys_params = IFTPhysicalParametersFormPresenter(
            phys_params=phys_params,
            view=self._view.content_phys_params)
        self.__cleanup_tasks.append(self._content_phys_params.destroy)

        # Image processing
        self._content_image_processing = IFTImageProcessingFormPresenter(
            image_annotator=image_annotator,
            create_image_acquisition_preview=_try_except(
                func=image_acquisition.create_preview,
                exc=ValueError, default=None),
            view=self._view.content_image_processing)
        self.__cleanup_tasks.append(self._content_image_processing.destroy)

        # Results
        self._content_results = IFTResultsPresenter(
            results_explorer=results_explorer,
            view=self._view.content_results)
        self.__cleanup_tasks.append(self._content_results.destroy)

        # Footer
        # Image acquisition
        self._footer_image_acquisition = LinearNavigatorFooterPresenter(
            back=None,
            next=IfThen(cond=self._content_image_acquisition.validate,
                        then=lambda: self._page_option_phys_params.set(True)),
            view=self._view.footer_image_acquisition)
        self.__cleanup_tasks.append(self._footer_image_acquisition.destroy)

        # Physical parameters
        self._footer_phys_params = LinearNavigatorFooterPresenter(
            back=lambda: self._page_option_image_acquisition.set(True),
            next=IfThen(cond=self._content_phys_params.validate,
                        then=lambda: self._page_option_image_processing.set(True)),
            view=self._view.footer_phys_params)
        self.__cleanup_tasks.append(self._footer_phys_params.destroy)

        # Image processing
        self._footer_image_processing = LinearNavigatorFooterPresenter(
            back=lambda: self._page_option_phys_params.set(True),
            next=IfThen(cond=self._content_image_processing.validate,
                        then=self._user_wants_to_start_analysis),
            view=self._view.footer_image_processing)
        self.__cleanup_tasks.append(self._footer_image_processing.destroy)

        # Sidebar
        self._sidebar_presenter = TasksSidebarPresenter(
            task_and_is_active=(
                (IFTWizardPageID.IMAGE_ACQUISITION, self._page_option_image_acquisition),
                (IFTWizardPageID.PHYS_PARAMS, self._page_option_phys_params),
                (IFTWizardPageID.IMAGE_PROCESSING, self._page_option_image_processing),
                (IFTWizardPageID.RESULTS, self._page_option_results)),
            view=self._view.sidebar_view)
        self.__cleanup_tasks.append(self._sidebar_presenter.destroy)

        event_connections.extend([
            self._page_option_image_acquisition.on_changed.connect(self._hdl_page_option_image_acquisition_changed,
                                                                   immediate=True),
            self._page_option_phys_params.on_changed.connect(self._hdl_page_option_phys_params_changed,
                                                             immediate=True),
            self._page_option_image_processing.on_changed.connect(self._hdl_page_option_image_processing_changed,
                                                                  immediate=True),
            self._page_option_results.on_changed.connect(self._hdl_page_option_results_changed,
                                                         immediate=True),
        ])

        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        # Activate the first page.
        self._page_option_image_acquisition.set(True)

    def _hdl_page_option_image_acquisition_changed(self) -> None:
        if self._page_option_image_acquisition.get() is True:
            self._content_image_acquisition.enter()
            self._view.active_content_view = self._view.content_image_acquisition
            self._view.active_footer_view = self._view.footer_image_acquisition
        else:
            self._content_image_acquisition.leave()

    def _hdl_page_option_phys_params_changed(self) -> None:
        if self._page_option_phys_params.get() is True:
            self._content_phys_params.enter()
            self._view.active_content_view = self._view.content_phys_params
            self._view.active_footer_view = self._view.footer_phys_params
        else:
            self._content_phys_params.leave()

    def _hdl_page_option_image_processing_changed(self) -> None:
        if self._page_option_image_processing.get() is True:
            self._content_image_processing.enter()
            self._view.active_content_view = self._view.content_image_processing
            self._view.active_footer_view = self._view.footer_image_processing
        else:
            self._content_image_processing.leave()

    def _hdl_page_option_results_changed(self) -> None:
        if self._page_option_results.get() is True:
            self._content_results.enter()
            self._view.active_content_view = self._view.content_results
            self._view.active_footer_view = self._view.footer_results
        else:
            pass
            self._content_results.leave()

    def _user_wants_to_start_analysis(self) -> None:
        analysis = self._create_analysis()
        self._results_explorer.analysis = analysis
        self._page_option_results.set(True)

    def destroy(self) -> None:
        for f in self.__cleanup_tasks:
            f()
        self.__cleanup_tasks = []


class IFTSpeaker(Speaker):
    def __init__(self, parent_content_stack: StackModel) -> None:
        super().__init__()

        self._loop = asyncio.get_event_loop()
        self.__cleanup_tasks = []  # type: MutableSequence[Callable[[], Any]]

        self._root_view = IFTRootView()
        self._root_presenter = None  # type: Optional[IFTRootPresenter]

        self._root_view_stack_key = object()
        self._root_view_parent_stack = parent_content_stack
        self._root_view_parent_stack.add_child(self._root_view_stack_key, self._root_view)

    def do_activate(self):
        self._loop.create_task(self._do_activate())

    async def _do_activate(self):
        # Create the analysis models

        # Image acquisition
        image_acquisition = ImageAcquisition()
        self.__cleanup_tasks.append(image_acquisition.destroy)

        # Set the initial image acquisition implementation to be 'local images'
        image_acquisition.type = DefaultImageAcquisitionImplType.LOCAL_IMAGES

        # Physical parameters
        phys_params_factory = IFTPhysicalParametersFactory()

        # Image annotator
        image_annotator = IFTImageAnnotator(image_acquisition.get_image_size_hint)

        tmp = Binding(phys_params_factory.bn_needle_width, image_annotator.bn_needle_width)
        self.__cleanup_tasks.append(tmp.unbind)

        # Analysis factory
        analysis_factory = IFTAnalysisFactory(image_acquisition, phys_params_factory, image_annotator)

        # Results explorer
        results_explorer = IFTResultsExplorer()

        self._root_presenter = IFTRootPresenter(
            image_acquisition=image_acquisition,
            phys_params=phys_params_factory,
            image_annotator=image_annotator,
            create_analysis=analysis_factory.create_analysis,
            results_explorer=results_explorer,
            view=self._root_view)
        self.__cleanup_tasks.append(self._root_presenter.destroy)

        # Make root view visible.
        self._root_view_parent_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self):
        for f in self.__cleanup_tasks:
            f()
        self.__cleanup_tasks = []
