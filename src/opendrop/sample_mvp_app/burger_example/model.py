from abc import abstractmethod
from enum import Enum
from typing import Generic, TypeVar, Union, Optional

from opendrop.mvp.Model import Model
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AbstractAtomicBindable

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
    def from_display(cls, display: str) -> 'MealSizeType':
        for enm in cls:
            if enm.display == display:
                return enm
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
        self._value = MealSizeType.from_display(value) if isinstance(value, str) else value


class BurgerOrder(Model):
    BASE_COST = 4.00

    MealSizeType = MealSizeType

    def __init__(self):
        super().__init__()

        self._v_cheese_slices = CheeseSlicesVar(0)
        self._v_bacon = BaconVar(False)
        self._v_meal_size = MealSizeVar(MealSizeType.SMALL)

        self._order = [self._v_cheese_slices, self._v_bacon, self._v_meal_size]

        self.bn_cheese_slices = AtomicBindableAdapter(
            getter=self._v_cheese_slices.get,
            setter=self._v_cheese_slices.set
        )

        self.bn_bacon = AtomicBindableAdapter(
            getter=self._v_bacon.get,
            setter=self._v_bacon.set
        )

        self.bn_meal_size = AtomicBindableAdapter(
            getter=self._v_meal_size.get,
            setter=self._v_meal_size.set
        )

        self.bn_order_cost = AtomicBindableAdapter(
            getter=self._calculate_order_cost
        )

        self.bn_cheese_slices.on_changed.connect(self.bn_order_cost.poke, ignore_args=True)
        self.bn_bacon.on_changed.connect(self.bn_order_cost.poke, ignore_args=True)
        self.bn_meal_size.on_changed.connect(self.bn_order_cost.poke, ignore_args=True)

    @AbstractAtomicBindable.property_adapter
    def cheese_slices(self): return self.bn_cheese_slices

    @AbstractAtomicBindable.property_adapter
    def bacon(self): return self.bn_bacon

    @AbstractAtomicBindable.property_adapter
    def meal_size(self): return self.bn_meal_size

    @AbstractAtomicBindable.property_adapter
    def order_cost(self): return self.bn_order_cost

    def _calculate_order_cost(self):
        order_cost = self.BASE_COST  # type: float

        for item in self._order:
            order_cost += item.price

        return order_cost
