import functools
from typing import Sequence

from opendrop.app.common.sidebar import WizardSidebarView
from .page import Page


class ActivePageIndicatorSidebarPresenter:
    def __init__(self, pages: Sequence[Page], view: WizardSidebarView) -> None:
        self._view = view
        self.__event_connections = []

        self._view.clear()

        for page in pages:
            view.add_task_name(page.name)
            page.control_switch.on_turned_on.connect(functools.partial(self._hdl_page_turned_on, page),
                                                     strong_ref=True, immediate=True)
            if page.control_switch.is_on:
                self._hdl_page_turned_on(page)

    def _hdl_page_turned_on(self, page: Page) -> None:
        self._view.bn_active_task_name.set(page.name)

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
