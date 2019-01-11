from abc import abstractmethod, ABC


class Form(ABC):
    @abstractmethod
    def validate(self) -> bool:
        """Validate this form."""
