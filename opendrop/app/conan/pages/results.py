from typing import Callable, Any, Optional

from opendrop.app.common.footer import OperationFooterModel, OperationFooterPresenter
from opendrop.app.common.wizard import WizardPagePresenter
from ..content.results import ConanResultsPresenter
from ..model.results_explorer import ConanResultsExplorer


class ConanResultsPagePresenter(WizardPagePresenter):
    __destroyed = False
    __cleanup_tasks = tuple()

    def _page_init(self,
                   results_explorer: ConanResultsExplorer,
                   user_wants_to_cancel_analysis: Callable[[], Any],
                   user_wants_to_save_analysis: Callable[[], Any],
                   back_action: Optional[Callable] = None) -> None:
        self._form = ConanResultsPresenter(results_explorer, self._view.form)
        self._footer = OperationFooterPresenter(
                model=OperationFooterModel(
                    operation=results_explorer.analysis,
                    back_action=back_action,
                    cancel_action=user_wants_to_cancel_analysis,
                    save_action=user_wants_to_save_analysis),
                view=self._view.footer)

        self.__cleanup_tasks = [self._form.destroy, self._footer.destroy]

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
