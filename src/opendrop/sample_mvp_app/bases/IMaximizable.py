from abc import abstractmethod


class IMaximizable:

    """Interface specifying that the view can be maximized.
    """

    @abstractmethod
    def maximize(self) -> None: pass

    @abstractmethod
    def unmaximize(self) -> None: pass