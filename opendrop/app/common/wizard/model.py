from typing import Iterable, Callable, Any

from opendrop.utility.bindable import BoxBindable


class WizardModel:
    def __init__(self, pages: Iterable[Any]) -> None:
        self._pages = tuple(pages)

        self._interpage_actions = {}

        self.bn_current_page = BoxBindable(self._pages[0])

    def next_page(self) -> None:
        current_page = self.bn_current_page.get()
        next_page_idx = self._pages.index(current_page) + 1
        next_page = self._pages[next_page_idx]

        self.perform_interpage_action(current_page, next_page)

        self.bn_current_page.set(next_page)

    def prev_page(self) -> None:
        current_page = self.bn_current_page.get()
        prev_page_idx = self._pages.index(current_page) - 1
        prev_page = self._pages[prev_page_idx]

        self.perform_interpage_action(current_page, prev_page)

        self.bn_current_page.set(prev_page)

    def perform_interpage_action(self, start_page: Any, end_page: Any) -> None:
        if (start_page, end_page) not in self._interpage_actions:
            return

        callback = self._interpage_actions[(start_page, end_page)]

        callback()

    def register_interpage_action(self, start_page: Any, end_page: Any, callback: Callable[[], Any]) -> None:
        self._interpage_actions[(start_page, end_page)] = callback


class WizardPageControls:
    def __init__(self, do_next_page: Callable[[], Any], do_prev_page: Callable[[], Any]) -> None:
        self._do_next_page = do_next_page
        self._do_prev_page = do_prev_page

    def next_page(self) -> None:
        self._do_next_page()

    def prev_page(self) -> None:
        self._do_prev_page()
