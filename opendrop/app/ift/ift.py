import asyncio
from pathlib import Path
from typing import Any, Callable, Optional, MutableSequence, Mapping

from gi.repository import Gtk

from opendrop.app.common.content.image_acquisition import ImageAcquisitionFormView
from opendrop.app.common.dialog import YesNoDialogView, YesNoDialogResponse, ErrorDialogView
from opendrop.app.common.footer import LinearNavigatorFooterView, OperationFooterView
from opendrop.app.common.model.image_acquisition.default_types import DefaultImageAcquisitionImplType
from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.wizard import WizardPresenter, WizardPageID, WizardView
from opendrop.component.stack import StackModel
from opendrop.utility.bindable import BoxBindable
from opendrop.utility.speaker import Speaker
from .content.analysis_saver import IFTAnalysisSaverPresenter, IFTAnalysisSaverView
from .content.image_processing import IFTImageProcessingFormView
from .content.phys_params import IFTPhysicalParametersFormView
from .content.results import IFTResultsView
from .model.analyser import IFTAnalysis
from .model.analysis_saver import IFTAnalysisSaverOptions, save_drops
from .model.image_annotator.image_annotator import IFTImageAnnotator
from .model.phys_params import IFTPhysicalParametersFactory
from .model.results_explorer import IFTResultsExplorer
from .pages import (
    IFTImageAcquisitionPagePresenter,
    IFTPhysicalParametersPagePresenter,
    IFTImageProcessingPagePresenter,
    IFTResultsPagePresenter
)


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

        tmp = image_annotator.bn_needle_width.bind_from(phys_params_factory.bn_needle_width)
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

        self.bn_current_analysis_done = BoxBindable(False)
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


class IFTWizardPageID(WizardPageID):
    IMAGE_ACQUISITION = ('Image acquisition',)
    PHYS_PARAMS = ('Physical parameters',)
    IMAGE_PROCESSING = ('Image processing',)
    RESULTS = ('Results',)


class IFTRootPresenter(WizardPresenter['IFTRootView', IFTWizardPageID]):
    def __init__(self, context: Context, view: 'IFTRootView'):
        super().__init__(
            view=view,
            page_entries=[
                self.PageEntry(
                    page_id=IFTWizardPageID.IMAGE_ACQUISITION,
                    presenter=IFTImageAcquisitionPagePresenter,
                    dependency_factory=self._get_dependencies_for_image_acquisition),
                self.PageEntry(
                    page_id=IFTWizardPageID.PHYS_PARAMS,
                    presenter=IFTPhysicalParametersPagePresenter,
                    dependency_factory=self._get_dependencies_for_phys_params),
                self.PageEntry(
                    page_id=IFTWizardPageID.IMAGE_PROCESSING,
                    presenter=IFTImageProcessingPagePresenter,
                    dependency_factory=self._get_dependencies_for_image_processing),
                self.PageEntry(
                    page_id=IFTWizardPageID.RESULTS,
                    presenter=IFTResultsPagePresenter,
                    dependency_factory=self._get_dependencies_for_results)])

        self._loop = asyncio.get_event_loop()
        self._context = context

        # Start the wizard flow
        self._activate_first_page()

    def _get_dependencies_for_image_acquisition(self) -> Mapping[str, Any]:
        return {'image_acquisition': self._context.image_acquisition,

                'next_action': self._next_page}

    def _get_dependencies_for_phys_params(self) -> Mapping[str, Any]:
        return {'phys_params': self._context.phys_params_factory,

                'back_action': self._prev_page,
                'next_action': self._next_page}

    def _get_dependencies_for_image_processing(self) -> Mapping[str, Any]:
        context = self._context

        try:
            preview = context.image_acquisition.create_preview()
        except ValueError:
            preview = None

        return {'image_annotator': context.image_annotator,
                'preview': preview,

                'back_action': self._prev_page,
                'next_action': self._user_wants_to_start_analysis}

    def _user_wants_to_start_analysis(self) -> None:
        self._context.new_analysis()
        self._next_page()

    def _get_dependencies_for_results(self) -> Mapping[str, Any]:
        return {'results_explorer': self._context.results_explorer,

                'user_wants_to_cancel_analysis': self._user_wants_to_cancel_analysis,
                'user_wants_to_save_analysis': self._user_wants_to_save_analysis,
                'back_action': self._user_wants_to_exit_analysis}

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

    def _user_wants_to_exit_analysis(self) -> None:
        context = self._context
        assert context.current_analysis_done

        def do_it(fut: Optional[asyncio.Future] = None) -> None:
            if fut is not None and (fut.cancelled() or fut.result() is False):
                return

            context.clear_current_analysis()
            self._prev_page()

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


class IFTRootView(WizardView[IFTWizardPageID]):
    def __init__(self) -> None:
        super().__init__()

        self._add_page(
            page_id=IFTWizardPageID.IMAGE_ACQUISITION,
            content=ImageAcquisitionFormView(),
            footer=LinearNavigatorFooterView())

        self._add_page(
            page_id=IFTWizardPageID.PHYS_PARAMS,
            content=IFTPhysicalParametersFormView(),
            footer=LinearNavigatorFooterView())

        self._add_page(
            page_id=IFTWizardPageID.IMAGE_PROCESSING,
            content=IFTImageProcessingFormView(),
            footer=LinearNavigatorFooterView(next_label='Start analysis'))

        self._add_page(
            page_id=IFTWizardPageID.RESULTS,
            content=IFTResultsView(),
            footer=OperationFooterView())

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


# This class is basically just used to help make "one liner's", not a great solution but works for now.

class IfThen:
    def __init__(self, cond: Callable, then: Callable) -> None:
        self._cond = cond
        self._then = then

    def __call__(self) -> None:
        if self._cond():
            self._then()
