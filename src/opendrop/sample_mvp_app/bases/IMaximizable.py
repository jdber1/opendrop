from abc import abstractmethod


class IMaximizable:
    @abstractmethod
    def maximize(self) -> None: pass

    @abstractmethod
    def unmaximize(self) -> None: pass