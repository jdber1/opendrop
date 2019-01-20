import asyncio
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, MutableSequence, TypeVar, Type, Union, Optional

from gi.repository import Gtk

from opendrop.app.common.content.image_acquisition import ImageAcquisitionFormPresenter, ImageAcquisitionFormView
from opendrop.app.common.dialog import YesNoDialogView, YesNoDialogResponse, ErrorDialogView
from opendrop.app.common.footer import LinearNavigatorFooterView, LinearNavigatorFooterPresenter, AnalysisFooterView, \
    AnalysisFooterPresenter
from opendrop.app.common.model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.sidebar import TasksSidebarPresenter, TasksSidebarView
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView
from opendrop.component.wizard.wizard import WizardPageID
from opendrop.utility.bindable.bindable import AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.events import EventConnection
from opendrop.utility.option import MutuallyExclusiveOptions
from opendrop.utility.speaker import Speaker
from .content.analysis_saver import IFTAnalysisSaverPresenter, IFTAnalysisSaverView
from .content.image_processing import IFTImageProcessingFormView, IFTImageProcessingFormPresenter
from .content.phys_params import IFTPhysicalParametersFormPresenter, IFTPhysicalParametersFormView
from .content.results import IFTResultsView, IFTResultsPresenter
from .footer import IFTAnalysisFooterModel
from .model.analyser import IFTAnalysis
from .model.analysis_factory import IFTAnalysisFactory
from .model.analysis_saver import IFTAnalysisSaverOptions, save_drops
from .model.image_annotator.image_annotator import IFTImageAnnotator
from .model.phys_params import IFTPhysicalParametersFactory
from .model.results_explorer import IFTResultsExplorer

# Helper functions

T = TypeVar('T')
U = TypeVar('U')


def _try_except(func: Callable[..., T], exc: Type[Exception], default: U) -> Callable[..., Union[T, U]]:
    def wrapper(*args, **kwargs) -> Union[T, U]:
        try:
            return func(*args, **kwargs)
        except exc:
            return default

    return wrapper


# Main classes start here

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
        self.footer_image_processing = LinearNavigatorFooterView(next_label='Start analysis')

        self.content_results = IFTResultsView()
        self.footer_results = AnalysisFooterView()

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

    @property
    def window(self) -> Optional[Gtk.Window]:
        toplevel = self.widget.get_toplevel()
        window = toplevel if isinstance(toplevel, Gtk.Window) else None
        return window

    def create_cancel_analysis_dialog(self) -> YesNoDialogView:
        return YesNoDialogView(message='Cancel analysis?', window=self.window)

    def create_discard_analysis_results_dialog(self) -> YesNoDialogView:
        return YesNoDialogView(message='Discard analysis results?', window=self.window)

    def create_clear_directory_dialog(self, path: Path) -> YesNoDialogView:
        return YesNoDialogView(
            message="This save location '{!s}' already exists, do you want to clear its contents?".format(path),
            window=self.window)

    def create_path_exists_and_is_not_a_directory_error_dialog(self, path: Path) -> ErrorDialogView:
        return ErrorDialogView(
            message="Cannot save to '{!s}', the path already exists and is a non-directory file.".format(path),
            window=self.window)

    def create_saver_dialog(self) -> IFTAnalysisSaverView:
        return IFTAnalysisSaverView(transient_for=self.window)


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
        self._loop = asyncio.get_event_loop()
        self._view = view
        self._create_analysis = create_analysis
        self._results_explorer = results_explorer

        self._current_analysis = None  # type: Optional[IFTAnalysis]
        self._current_analysis_saved = False

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

        # Results
        self._footer_results_model = IFTAnalysisFooterModel(
            back_action=self._user_wants_to_exit_analysis,
            cancel_action=self._user_wants_to_cancel_analysis,
            save_action=self._user_wants_to_save_analysis)
        self._footer_results = AnalysisFooterPresenter(
            model=self._footer_results_model,
            view=self._view.footer_results)  # type: Optional[AnalysisFooterPresenter]
        self.__cleanup_tasks.append(self._footer_results.destroy)
        self.__cleanup_tasks.append(self._footer_results_model.destroy)
        self.__cleanup_tasks.append(
            Binding(self._results_explorer.bn_analysis, self._footer_results_model.bn_analysis).unbind)

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
            self._page_option_image_acquisition.on_changed.connect(self._hdl_page_option_image_acquisition_changed),
            self._page_option_phys_params.on_changed.connect(self._hdl_page_option_phys_params_changed),
            self._page_option_image_processing.on_changed.connect(self._hdl_page_option_image_processing_changed),
            self._page_option_results.on_changed.connect(self._hdl_page_option_results_changed)])
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        # Activate the first page.
        self._page_option_image_acquisition.set(True)

    def _user_wants_to_start_analysis(self) -> None:
        analysis = self._create_analysis()

        self._current_analysis = analysis
        self._current_analysis_saved = False

        self._results_explorer.analysis = analysis
        self._page_option_results.set(True)

    def _user_wants_to_cancel_analysis(self) -> None:
        analysis = self._results_explorer.analysis
        if analysis is None or analysis.cancelled:
            return

        confirm_cancel_analysis = self._loop.create_task(self._ask_user_confirm_cancel_analysis())
        early_termination_ec = analysis.bn_done.on_changed.connect(
            IfThen(cond=analysis.bn_done.get,
                   then=confirm_cancel_analysis.cancel),
            weak_ref=False)

        def result(fut: asyncio.Future) -> None:
            early_termination_ec.disconnect()
            if fut.cancelled() or fut.result() is False:
                return
            analysis.cancel()

        confirm_cancel_analysis.add_done_callback(result)

    def _user_wants_to_exit_analysis(self) -> None:
        assert self._current_analysis.bn_done.get()

        def done(fut: Optional[asyncio.Future] = None) -> None:
            if fut is not None and (fut.cancelled() or fut.result() is False):
                return
            self._page_option_image_processing.set(True)

        if not self._current_analysis_saved:
            self._loop.create_task(self._ask_user_confirm_discard_analysis_results()).add_done_callback(done)
        else:
            done()

    def _user_wants_to_save_analysis(self) -> None:
        analysis = self._current_analysis
        if analysis is None or not analysis.bn_done.get():
            return

        def done(fut: asyncio.Future) -> None:
            if fut.cancelled():
                return

            options = fut.result()  # type: IFTAnalysisSaverOptions
            if options is None:
                return

            self._save_analysis(options)

        self._loop.create_task(self._ask_user_save_analysis()).add_done_callback(done)

    def _save_analysis(self, save_options: IFTAnalysisSaverOptions) -> None:
        analysis = self._current_analysis
        assert analysis is not None and analysis.bn_done.get()

        save_drops(analysis.drops, save_options)
        self._current_analysis_saved = True

    async def _ask_user_confirm_discard_analysis_results(self) -> bool:
        dlg_view = self._view.create_discard_analysis_results_dialog()
        try:
            dlg_response = await dlg_view.on_response.wait()
            return dlg_response is YesNoDialogResponse.YES
        finally:
            dlg_view.destroy()

    async def _ask_user_confirm_cancel_analysis(self) -> bool:
        dlg_view = self._view.create_cancel_analysis_dialog()
        try:
            dlg_response = await dlg_view.on_response.wait()
            return dlg_response is YesNoDialogResponse.YES
        finally:
            dlg_view.destroy()

    async def _ask_user_save_analysis(self) -> Optional[IFTAnalysisSaverOptions]:
        options = IFTAnalysisSaverOptions()

        while True:
            save_dlg_view = self._view.create_saver_dialog()
            save_dlg = IFTAnalysisSaverPresenter(options, save_dlg_view)

            try:
                accept = await save_dlg.on_user_finished_editing.wait()
            finally:
                save_dlg.destroy()
                save_dlg_view.destroy()

            if not accept:
                return

            save_root_dir = options.save_root_dir
            if not save_root_dir.exists():
                # User specified a non-existent directory, we will create one later.
                break
            elif save_root_dir.is_dir():
                if len(tuple(save_root_dir.iterdir())) == 0:
                    # Directory is empty, no 'overwrite' confirmation required.
                    break

                user_wants_to_clear_dir = await self._ask_user_clear_directory(save_root_dir)
                if user_wants_to_clear_dir:
                    break
                else:
                    # User does not want to clear the existing directory, return to save options dialog.
                    continue
            else:
                # Path exists, but is not a directory. We will not attempt to remove whatever it is.
                await self._tell_user_file_exists_and_is_not_a_directory(save_root_dir)
                continue

        return options

    async def _ask_user_clear_directory(self, path: Path) -> None:
        dlg_view = self._view.create_clear_directory_dialog(path)
        try:
            dlg_response = await dlg_view.on_response.wait()
            return dlg_response is YesNoDialogResponse.YES
        finally:
            dlg_view.destroy()

    async def _tell_user_file_exists_and_is_not_a_directory(self, path: Path) -> None:
        dlg_view = self._view.create_path_exists_and_is_not_a_directory_error_dialog(path)
        try:
            await dlg_view.on_acknowledged.wait()
        finally:
            dlg_view.destroy()

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
            self._content_results.leave()

    def destroy(self) -> None:
        for f in self.__cleanup_tasks:
            f()
        self.__cleanup_tasks = []

        if self._current_analysis is not None:
            self._current_analysis.cancel()


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
