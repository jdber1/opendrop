from abc import abstractmethod
from enum import Enum
from typing import Generic, TypeVar, Union, Any, Mapping, Optional, Dict

from opendrop.mvp.Model import Model

T = TypeVar('T')


class MealSizeType(Enum):
    SMALL = ('Small', 0.00)
    MEDIUM = ('Medium', 1.00)
    LARGE = ('Large', 1.50)
    SUPERSIZE = ('Supersize', 1.90)

    def __init__(self, display: str, price: Optional[float] = None):
        self.id = len(type(self).__members__) + 1

        self.display = display  # type: str
        self.price = price  # type: float

    @classmethod
    def from_display_string(cls, display: str) -> 'MealSizeType':
        for e in cls:
            if e.display == display:
                return e
        else:
            raise ValueError

    def __str__(self) -> str:
        return self.display

    def __int__(self) -> int:
        return self.id


class BurgerItemVar(Generic[T]):
    @property
    @abstractmethod
    def price(self) -> float: pass

    @abstractmethod
    def get(self) -> T: pass

    @abstractmethod
    def set(self, value: T) -> None: pass


class BaconVar(BurgerItemVar[bool]):
    PRICE = 1.95  # type: float

    def __init__(self, value: bool):
        self._value = value  # type: bool

    @property
    def price(self) -> float:
        return self.PRICE * self._value

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = value


class CheeseSlicesVar(BurgerItemVar[int]):
    PRICE = 0.50  # type: float

    def __init__(self, value: int):
        self._value = value  # type: int

    @property
    def price(self) -> float:
        return self.PRICE * self._value

    def get(self) -> int:
        return self._value

    def set(self, value: int) -> None:
        self._value = value


class MealSizeVar(BurgerItemVar[MealSizeType]):
    def __init__(self, value: MealSizeType):
        self._value = value  # type: MealSizeType

    @property
    def price(self) -> float:
        return self.get().price

    def get(self) -> MealSizeType:
        return self._value

    def set(self, value: Union[MealSizeType, str]) -> None:
        self._value = MealSizeType.from_display_string(value) if isinstance(value, str) else value


class BurgerOrder(Model):
    BASE_COST = 4.00

    MealSizeType = MealSizeType

    def __init__(self):
        super().__init__()

        self._order = {
            'cheese_slices': CheeseSlicesVar(0),
            'bacon': BaconVar(False),
            'meal_size': MealSizeVar(MealSizeType.SMALL)
        }  # type: Dict[str, BurgerItemVar]

        self._cache = {
            name: item.get() for name, item in self._order.items()
        }

    def check_for_changes(self) -> None:
        for name, order_value in self.order.items():
            if self._cache[name] != order_value:
                self._cache[name] = order_value

                self.fire('on_order_changed', name, order_value)

    @property
    def order(self) -> Mapping[str, BurgerItemVar]:
        return {name: item.get() for name, item in self._order.items()}

    def edit_order(self, name: str, new_value: Any) -> None:
        self._order[name].set(new_value)

        self.check_for_changes()

        self.fire('on_order_cost_changed')

    @property
    def order_cost(self) -> float:
        order_cost = self.BASE_COST  # type: float

        for item in self._order.values():
            order_cost += item.price

        return order_cost
