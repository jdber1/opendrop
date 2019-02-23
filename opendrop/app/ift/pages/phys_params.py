from typing import Optional, Callable

from opendrop.app.common.footer import LinearNavigatorFooterPresenter
from opendrop.app.common.wizard import WizardPagePresenter
from ..content.phys_params import IFTPhysicalParametersFormPresenter
from ..model.phys_params import IFTPhysicalParametersFactory


class IFTPhysicalParametersPagePresenter(WizardPagePresenter):
    __destroyed = False
    __cleanup_tasks = tuple()

    def _page_init(self,
                   phys_params: IFTPhysicalParametersFactory,
                   back_action: Optional[Callable] = None,
                   next_action: Optional[Callable] = None) -> None:
        self._next_action = next_action

        self._form = IFTPhysicalParametersFormPresenter(phys_params, self._view.form)
        self._footer = LinearNavigatorFooterPresenter(
            back=back_action,
            next=self._hdl_footer_next if next_action is not None else None,
            view=self._view.footer)

        self.__cleanup_tasks = [self._form.destroy, self._footer.destroy]

    def _hdl_footer_next(self) -> None:
        next_action = self._next_action
        assert next_action is not None

        if not self._form.validate():
            return

        next_action()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
