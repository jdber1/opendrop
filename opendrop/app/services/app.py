from typing import Any, Callable


class OpendropService:
    def __init__(
            self,
            do_main_menu: Callable[[], Any],
            do_ift: Callable[[], Any],
            do_conan: Callable[[], Any],
            do_quit: Callable[[], Any],
    ) -> None:
        self._do_main_menu = do_main_menu
        self._do_ift = do_ift
        self._do_conan = do_conan
        self._do_quit = do_quit

    def goto_main_menu(self) -> None:
        self._do_main_menu()

    def goto_ift(self) -> None:
        self._do_ift()

    def goto_conan(self) -> None:
        self._do_conan()

    def quit(self) -> None:
        self._do_quit()
