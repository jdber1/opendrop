from typing import Callable, Any


class MainMenuModel:
    def __init__(
            self,
            do_launch_ift:  Callable[[], Any],
            do_launch_conan:  Callable[[], Any],
            do_exit: Callable[[], Any]
    ) -> None:
        self._do_launch_ift = do_launch_ift
        self._do_launch_conan = do_launch_conan
        self._do_exit = do_exit

    def launch_ift(self) -> None:
        self._do_launch_ift()

    def launch_conan(self) -> None:
        self._do_launch_conan()

    def exit(self) -> None:
        self._do_exit()
