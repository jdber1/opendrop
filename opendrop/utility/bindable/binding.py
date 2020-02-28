import functools
from typing import Callable, Generic, TypeVar, overload, Union

from . import typing

_T = TypeVar('_T')
_U = TypeVar('_U')


class Binding(typing.Binding, Generic[_T, _U]):
    def __init__(
            self,
            src: Union[typing.ReadBindable[_T], typing.Bindable[_T]],
            dst: Union[typing.WriteBindable[_U], typing.Bindable[_U]],
            to_dst: Callable[[_T], _U] = lambda x: x,
            to_src: Callable[[_U], _T] = lambda x: x,
            *,
            one_way: bool = False
    ) -> None:
        self._src = src
        self._dst = dst

        self._to_dst = to_dst
        self._to_src = to_src

        self._on_changed_conns = [
            bn.on_changed.connect(functools.partial(self._hdl_bindable_changed, bn), weak_ref=False)
            for bn in ((src, dst) if not one_way else (src,))
        ]

        # Update the value of `dst` to the current value of `src`.
        self._hdl_bindable_changed(src)

    @overload
    def _hdl_bindable_changed(self, from_: typing.ReadBindable[_T]) -> None: ...

    @overload
    def _hdl_bindable_changed(self, from_: typing.ReadBindable[_U]) -> None: ...

    def _hdl_bindable_changed(self, from_) -> None:
        target = self._get_target(from_)

        new_value = from_.get()
        new_value = self._transform_value(new_value, target=target)

        target.set(new_value)

    @overload
    def _get_target(self, this: typing.ReadBindable[_T]) -> typing.WriteBindable[_U]: ...

    @overload
    def _get_target(self, this: typing.ReadBindable[_U]) -> typing.WriteBindable[_T]: ...

    def _get_target(self, this):
        """Return the `src` Bindable if `this` is `dst`, else return the `dst` Bindable."""
        assert this in (self._src, self._dst)

        if this is self._src:
            return self._dst
        else:
            return self._src

    @overload
    def _transform_value(self, value: _T, target: typing.WriteBindable[_U]) -> _U: ...

    @overload
    def _transform_value(self, value: _U, target: typing.WriteBindable[_T]) -> _T: ...

    def _transform_value(self, value, target):
        assert target in (self._src, self._dst)

        if target is self._dst:
            return self._to_dst(value)
        else:
            return self._to_src(value)

    def unbind(self) -> None:
        for conn in self._on_changed_conns:
            conn.disconnect()

        del self._src
        del self._dst

        del self._to_dst
        del self._to_src

        # Delete the connections as well since they also hold a reference to `_src` and `_dst` (through the
        # functools.partial object).
        del self._on_changed_conns
