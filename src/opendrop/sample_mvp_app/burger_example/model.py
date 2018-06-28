from abc import abstractmethod
from enum import Enum
from typing import Generic, TypeVar, Union, Any, Mapping, Optional, Dict, Tuple

from opendrop.mvp.Model import Model
from opendrop.utility import data_binding

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
            print(display)
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

        self._cheese_slices = CheeseSlicesVar(0)
        self._bacon = BaconVar(False)
        self._meal_size = MealSizeVar(MealSizeType.SMALL)

    @data_binding.property
    def cheese_slices(self) -> int:
        return self._cheese_slices.get()

    @cheese_slices.setter
    def cheese_slices(self, value: int):
        self._cheese_slices.set(value)

        self.update_order_cost()

    @data_binding.property
    def bacon(self) -> bool:
        return self._bacon.get()

    @bacon.setter
    def bacon(self, value: bool) -> None:
        self._bacon.set(value)

        self.update_order_cost()

    @data_binding.property
    def meal_size(self) -> MealSizeType:
        return self._meal_size.get()

    @meal_size.setter
    def meal_size(self, value: MealSizeType) -> None:
        self._meal_size.set(value)

        self.update_order_cost()

    @data_binding.property
    def order_cost(self) -> float:
        return self._order_cost

    @order_cost.setter
    def order_cost(self, value: float) -> None:
        self._order_cost = value

    @property
    def order(self) -> Tuple[BurgerItemVar, ...]:
        return self._cheese_slices, self._bacon, self._meal_size

    def update_order_cost(self):
        order_cost = self.BASE_COST  # type: float

        for item in self.order:
            order_cost += item.price

        self.order_cost = order_cost
