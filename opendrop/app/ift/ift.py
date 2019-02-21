import asyncio
from enum import Enum
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, TypeVar, Type, Union, Optional, MutableSequence

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
from opendrop.utility.bindable.bindable import AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.option import MutuallyExclusiveOptions
from opendrop.utility.speaker import Speaker
from .content.analysis_saver import IFTAnalysisSaverPresenter, IFTAnalysisSaverView
from .content.image_processing import IFTImageProcessingFormView, IFTImageProcessingFormPresenter
from .content.phys_params import IFTPhysicalParametersFormPresenter, IFTPhysicalParametersFormView
from .content.results import IFTResultsView, IFTResultsPresenter
from .footer import IFTAnalysisFooterModel
from .model.analyser import IFTAnalysis
from .model.analysis_saver import IFTAnalysisSaverOptions, save_drops
from .model.image_annotator.image_annotator import IFTImageAnnotator
from .model.phys_params import IFTPhysicalParametersFactory
from .model.results_explorer import IFTResultsExplorer


class IFTSpeaker(Speaker):
    def __init__(self, parent_content_stack: StackModel) -> None:
        super().__init__()

        self._loop = asyncio.get_event_loop()

        self.__active = False
        self.__cleanup_tasks = []  # type: MutableSequence[Callable[[], Any]]

        self._root_view = IFTRootView()
        self._root_presenter = None  # type: Optional[IFTRootPresenter]

        self._root_view_stack_key = object()
        self._root_view_parent_stack = parent_content_stack
        self._root_view_parent_stack.add_child(self._root_view_stack_key, self._root_view)

    def do_activate(self):
        self.__active = True
        self.__cleanup_tasks.clear()

        # Create the analysis models

        # Image acquisition
        image_acquisition = ImageAcquisition()
        # Set the initial image acquisition implementation to be 'local images'
        image_acquisition.type = DefaultImageAcquisitionImplType.LOCAL_IMAGES
        self.__cleanup_tasks.append(image_acquisition.destroy)

        # Physical parameters
        phys_params_factory = IFTPhysicalParametersFactory()

        # Image annotator
        image_annotator = IFTImageAnnotator(image_acquisition.get_image_size_hint)

        tmp = Binding(phys_params_factory.bn_needle_width, image_annotator.bn_needle_width)
        self.__cleanup_tasks.append(tmp.unbind)

        # Results explorer
        results_explorer = IFTResultsExplorer()

        context = Context(image_acquisition, phys_params_factory, image_annotator, results_explorer)
        self.__cleanup_tasks.append(context.destroy)

        self._root_presenter = IFTRootPresenter(context, view=self._root_view)
        self.__cleanup_tasks.append(self._root_presenter.destroy)

        # Make root view visible.
        self._root_view_parent_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self):
        if not self.__active:
            return

        for f in self.__cleanup_tasks:
            f()

        self.__active = False


class Context:
    _current_analysis_value = None  # type: Optional[IFTAnalysis]
    _current_analysis_saved = False

    def __init__(self,
                 image_acquisition: ImageAcquisition,
                 phys_params_factory: IFTPhysicalParametersFactory,
                 image_annotator: IFTImageAnnotator,
                 results_explorer: IFTResultsExplorer) -> None:
        self.image_acquisition = image_acquisition
        self.phys_params_factory = phys_params_factory
        self.image_annotator = image_annotator
        self.results_explorer = results_explorer

        self.bn_current_analysis_done = AtomicBindableVar(False)
        self._analysis_unbind_tasks = []

    def new_analysis(self) -> None:
        analysis = IFTAnalysis(
            scheduled_images=self.image_acquisition.acquire_images(),
            annotate_image=self.image_annotator.annotate_image,
            phys_params=self.phys_params_factory.create_physical_parameters())

        self._current_analysis = analysis
        self._current_analysis_saved = False

    def clear_current_analysis(self) -> None:
        self.cancel_current_analysis()

        self._current_analysis = None
        self._current_analysis_saved = False

    def cancel_current_analysis(self) -> None:
        analysis = self._current_analysis
        if analysis is None:
            return

        analysis.cancel()

    def save_current_analysis(self, options: IFTAnalysisSaverOptions) -> None:
        analysis = self._current_analysis
        if analysis is None:
            raise ValueError('Cannot save, no current analysis exists')
        if not analysis.bn_done.get():
            raise ValueError('Cannot save, current analysis is not done')

        save_drops(analysis.drop_analyses, options)
        self._current_analysis_saved = True

    @property
    def _current_analysis(self) -> Optional[IFTAnalysis]:
        return self._current_analysis_value

    @_current_analysis.setter
    def _current_analysis(self, analysis: Optional[IFTAnalysis]) -> None:
        self._unbind_current_analysis()

        self._current_analysis_value = analysis
        self.results_explorer.analysis = analysis

        if analysis is not None:
            self._bind_analysis(analysis)

    def _unbind_current_analysis(self) -> None:
        for f in self._analysis_unbind_tasks:
            f()
        self._analysis_unbind_tasks = []

    def _bind_analysis(self, analysis):
        data_bindings = [
            self.bn_current_analysis_done.bind_from(analysis.bn_done)]
        self._analysis_unbind_tasks.extend(db.unbind for db in data_bindings)

    @property
    def current_analysis_exists(self) -> bool:
        return self._current_analysis is not None

    @property
    def current_analysis_saved(self) -> bool:
        return self._current_analysis_saved

    @property
    def current_analysis_done(self) -> bool:
        return self.bn_current_analysis_done.get()

    def destroy(self) -> None:
        self.clear_current_analysis()


class IFTRootPresenter:
    def __init__(self, context: Context, view: 'IFTRootView'):
        self._loop = asyncio.get_event_loop()

        self._context = context
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

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

        image_acquisition = context.image_acquisition
        phys_params = context.phys_params_factory
        image_annotator = context.image_annotator
        results_explorer = context.results_explorer

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
            create_preview=_try_except(
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
            Binding(results_explorer.bn_analysis, self._footer_results_model.bn_analysis).unbind)

        # Sidebar
        self._sidebar_presenter = TasksSidebarPresenter(
            task_and_is_active=(
                (IFTWizardPageID.IMAGE_ACQUISITION, self._page_option_image_acquisition),
                (IFTWizardPageID.PHYS_PARAMS, self._page_option_phys_params),
                (IFTWizardPageID.IMAGE_PROCESSING, self._page_option_image_processing),
                (IFTWizardPageID.RESULTS, self._page_option_results)),
            view=self._view.sidebar_view)
        self.__cleanup_tasks.append(self._sidebar_presenter.destroy)

        event_connections = [
            self._page_option_image_acquisition.on_changed.connect(self._hdl_page_option_image_acquisition_changed),
            self._page_option_phys_params.on_changed.connect(self._hdl_page_option_phys_params_changed),
            self._page_option_image_processing.on_changed.connect(self._hdl_page_option_image_processing_changed),
            self._page_option_results.on_changed.connect(self._hdl_page_option_results_changed)]
        self.__cleanup_tasks.extend([ec.disconnect for ec in event_connections])

        # Activate the first page.
        self._page_option_image_acquisition.set(True)

    def _user_wants_to_start_analysis(self) -> None:
        self._context.new_analysis()
        self._page_option_results.set(True)

    def _user_wants_to_save_analysis(self) -> None:
        context = self._context
        if not context.current_analysis_done:
            return

        def done(fut: asyncio.Future) -> None:
            if fut.cancelled():
                return

            options = fut.result()  # type: IFTAnalysisSaverOptions
            if options is None:
                return

            self._context.save_current_analysis(options)

        self._loop.create_task(self._ask_user_save_analysis()).add_done_callback(done)

    def _user_wants_to_cancel_analysis(self) -> None:
        context = self._context
        if not context.current_analysis_exists or context.current_analysis_done:
            return

        confirm_cancel_analysis = self._loop.create_task(self._ask_user_confirm_cancel_analysis())
        early_termination_conn = context.bn_current_analysis_done.on_changed.connect(
            IfThen(cond=context.bn_current_analysis_done.get,
                   then=confirm_cancel_analysis.cancel),
            weak_ref=False)

        def do_it(fut: asyncio.Future) -> None:
            early_termination_conn.disconnect()
            if fut.cancelled() or fut.result() is False:
                return
            context.cancel_current_analysis()

        confirm_cancel_analysis.add_done_callback(do_it)

    def _user_wants_to_exit_analysis(self) -> None:
        context = self._context
        assert context.current_analysis_done

        def do_it(fut: Optional[asyncio.Future] = None) -> None:
            if fut is not None and (fut.cancelled() or fut.result() is False):
                return

            context.clear_current_analysis()
            self._page_option_image_processing.set(True)

        if not context.current_analysis_saved:
            self._loop.create_task(self._ask_user_confirm_discard_analysis_results()).add_done_callback(do_it)
        else:
            do_it()

    save_dlg = None

    async def _ask_user_save_analysis(self) -> Optional[IFTAnalysisSaverOptions]:
        if self.save_dlg is not None:
            # Save dialog is already open
            return

        options = IFTAnalysisSaverOptions()

        while True:
            save_dlg_view = self._view.create_saver_dialog()
            self.save_dlg = IFTAnalysisSaverPresenter(options, save_dlg_view)
            try:
                accept = await self.save_dlg.on_user_finished_editing.wait()
            finally:
                self.save_dlg.destroy()
                self.save_dlg = None
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

    async def _ask_user_confirm_cancel_analysis(self) -> bool:
        dlg_view = self._view.create_cancel_analysis_dialog()
        try:
            dlg_response = await dlg_view.on_response.wait()
            return dlg_response is YesNoDialogResponse.YES
        finally:
            dlg_view.destroy()

    async def _ask_user_confirm_discard_analysis_results(self) -> bool:
        dlg_view = self._view.create_discard_analysis_results_dialog()
        try:
            dlg_response = await dlg_view.on_response.wait()
            return dlg_response is YesNoDialogResponse.YES
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
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class IFTWizardPageID(Enum):
    IMAGE_ACQUISITION = ('Image acquisition',)
    PHYS_PARAMS = ('Physical parameters',)
    IMAGE_PROCESSING = ('Image processing',)
    RESULTS = ('Results',)

    def __init__(self, title: str) -> None:
        self.title = title


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

    def _set_active_content_view(self, view: GtkWidgetView) -> None:
        self._content_view.set_visible_child(view)

    active_content_view = property(fset=_set_active_content_view)

    def _set_active_footer_view(self, view: GtkWidgetView) -> None:
        self._footer_view.set_visible_child(view)

    active_footer_view = property(fset=_set_active_footer_view)

    @property
    def window(self) -> Optional[Gtk.Window]:
        toplevel = self.widget.get_toplevel()
        window = toplevel if isinstance(toplevel, Gtk.Window) else None
        return window

    def create_cancel_analysis_dialog(self) -> YesNoDialogView:
        return YesNoDialogView(
            message='Cancel analysis?',
            window=self.window)

    def create_discard_analysis_results_dialog(self) -> YesNoDialogView:
        return YesNoDialogView(
            message='Discard analysis results?',
            window=self.window)

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


# Helper functions/classes

T = TypeVar('T')
U = TypeVar('U')


# These functions and classes are basically just used to help make "one liner's", not a great solution but works for
# now.

def _try_except(func: Callable[..., T], exc: Type[Exception], default: U) -> Callable[..., Union[T, U]]:
    def wrapper(*args, **kwargs) -> Union[T, U]:
        try:
            return func(*args, **kwargs)
        except exc:
            return default

    return wrapper


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
