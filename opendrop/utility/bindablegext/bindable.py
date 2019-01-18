import weakref
from typing import Any, Callable

from gi.repository import GObject

from opendrop.utility.bindable.bindable import AtomicBindableAdapter, BaseAtomicBindable


def _identity(x):
    return x


class AtomicBindableAdapterGPropLink:
    def __init__(self, bn: AtomicBindableAdapter, g_obj: GObject.Object, prop_name: str,
                 transform_to: Callable = _identity, transform_from: Callable = _identity) -> None:
        if bn.getter is not None:
            raise ValueError(
                'AtomicBindableAdapter ({0}) already has a getter ({0.getter}) function'
                    .format(bn)
            )
        elif bn.setter is not None:
            raise ValueError(
                'AtomicBindableAdapter ({0}) already has a setter ({0.setter}) function'
                    .format(bn)
            )

        self._alive = True
        self._bn = bn

        # For some reason, it seems like the GObject can be garbage collected before this object is garbage collected,
        # the following workaround uses _g_obj_wr to check if g_obj has been garbage collected by seeing if _g_obj_wr()
        # returns None.
        self._g_obj = g_obj
        self._g_obj_wr = weakref.ref(g_obj)

        self._prop_name = prop_name

        self._transform_to = transform_to
        self._transform_from = transform_from

        bn.getter = self._getter
        bn.setter = self._setter

        self._hdl_g_obj_notify_id = self._g_obj.connect('notify::{}'.format(prop_name), self._hdl_g_obj_notify)

    def _getter(self) -> Any:
        value = self._g_obj.get_property(self._prop_name)
        return self._transform_from(value)

    def _setter(self, value: Any) -> None:
        self._g_obj.handler_block(self._hdl_g_obj_notify_id)
        value = self._transform_to(value)
        self._g_obj.set_property(self._prop_name, value)
        self._g_obj.handler_unblock(self._hdl_g_obj_notify_id)

    def _hdl_g_obj_notify(self, g_obj: GObject.Object, pspec: GObject.GParamSpec) -> None:
        if not self._alive:
            return
        self._bn.poke()

    @property
    def _is_g_obj_garbage_collected(self) -> bool:
        return self._g_obj_wr() is None

    def unlink(self, *_):
        if not self._alive:
            return

        if not self._is_g_obj_garbage_collected and self._g_obj.handler_is_connected(self._hdl_g_obj_notify_id):
            self._g_obj.disconnect(self._hdl_g_obj_notify_id)

        self._bn.getter = None
        self._bn.setter = None
        self._alive = False

    def __del__(self):
        self.unlink()


# Give the class a more 'function-y' sounding name.
link_atomic_bn_adapter_to_g_prop = AtomicBindableAdapterGPropLink


class GObjectPropertyBindable(BaseAtomicBindable):
    def __init__(self, g_obj: GObject.Object, prop_name: str, transform_to: Callable = _identity,
                 transform_from: Callable = _identity) -> None:
        super().__init__()

        self._alive = True

        # For some reason, it seems like the GObject can be garbage collected before this object is garbage collected,
        # the following workaround uses _g_obj_wr to check if g_obj has been garbage collected by seeing if _g_obj_wr()
        # returns None.
        self._g_obj = g_obj
        self._g_obj_wr = weakref.ref(g_obj)

        self._prop_name = prop_name

        self._transform_to = transform_to
        self._transform_from = transform_from

        self._hdl_g_obj_notify_id = self._g_obj.connect('notify::{}'.format(prop_name), self._hdl_g_obj_notify)

    def _raw_get(self) -> Any:
        assert self._alive
        value = self._g_obj.get_property(self._prop_name)
        return self._transform_from(value)

    def _raw_set(self, value: Any) -> None:
        assert self._alive
        self._g_obj.handler_block(self._hdl_g_obj_notify_id)
        value = self._transform_to(value)
        self._g_obj.set_property(self._prop_name, value)
        self._g_obj.handler_unblock(self._hdl_g_obj_notify_id)

    def _hdl_g_obj_notify(self, g_obj: GObject.Object, pspec: GObject.GParamSpec) -> None:
        if not self._alive:
            return
        self.poke()

    @property
    def _is_g_obj_garbage_collected(self) -> bool:
        return self._g_obj_wr() is None

    def unlink(self, *_):
        if not self._alive:
            return

        if not self._is_g_obj_garbage_collected and self._g_obj.handler_is_connected(self._hdl_g_obj_notify_id):
            self._g_obj.disconnect(self._hdl_g_obj_notify_id)

        self._alive = False

    def __del__(self):
        self.unlink()
