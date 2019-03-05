import functools
from typing import Callable, Generic, TypeVar, overload

from opendrop.utility.simplebindable.bindable import Bindable

_T = TypeVar('_T')
_U = TypeVar('_U')


class Binding(Generic[_T, _U]):
    def __init__(self, src: Bindable[_T], dst: Bindable[_U], to_dst: Callable[[_T], _U] = lambda x: x,
                 to_src: Callable[[_U], _T] = lambda x: x) -> None:
        self._src = src
        self._dst = dst

        self._to_dst = to_dst
        self._to_src = to_src

        self._on_changed_conns = {
            id(bn): bn.on_changed.connect(functools.partial(self._hdl_bindable_changed, bn), weak_ref=False)
            for bn in (src, dst)}

        # Update the value of `dst` to the current value of `src`.
        self._hdl_bindable_changed(src)

    @overload
    def _hdl_bindable_changed(self, from_: Bindable[_T]) -> None:
        ...
    @overload
    def _hdl_bindable_changed(self, from_: Bindable[_U]) -> None:
        ...
    def _hdl_bindable_changed(self, from_) -> None:
        target = self._get_other(from_)
        target.set(self._transform_value(from_.get(), target=target))

    @overload
    def _get_other(self, this: Bindable[_T]) -> Bindable[_U]:
        ...
    @overload
    def _get_other(self, this: Bindable[_U]) -> Bindable[_T]:
        ...
    def _get_other(self, this):
        """Return the `src` bindable if `this` is `dst`, else return the `dst` bindable."""
        assert this in (self._src, self._dst)

        if this is self._src:
            return self._dst
        else:
            return self._src

    @overload
    def _transform_value(self, value: _T, target: Bindable[_U]) -> _U:
        ...
    @overload
    def _transform_value(self, value: _U, target: Bindable[_T]) -> _T:
        ...
    def _transform_value(self, value, target):
        assert target in (self._src, self._dst)

        if target is self._dst:
            return self._to_dst(value)
        else:
            return self._to_src(value)

    def unbind(self) -> None:
        """Unbind the bound bindables, new transactions in one will no longer be applied to the other. This Binding will
        will also no longer hold a reference to the bounded bindables.
        """
        for conn in self._on_changed_conns.values():
            conn.disconnect()

        del self._src
        del self._dst

        del self._to_dst
        del self._to_src

        # Delete the connections as well since they also hold a reference to `_src` and `_dst` (through the
        # functools.partial object).
        del self._on_changed_conns
