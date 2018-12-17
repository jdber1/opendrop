from typing import Any

from gi.repository import GObject

from opendrop.utility.bindable.bindable import AtomicBindableAdapter


class AtomicBindableAdapterGPropLink:
    def __init__(self, bn: AtomicBindableAdapter, g_obj: GObject.Object, prop_name: str):
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

        self._bn = bn
        self._g_obj = g_obj
        self._prop_name = prop_name

        bn.getter = self._getter
        bn.setter = self._setter
        self._hdl_g_obj_notify_id = self._g_obj.connect('notify::{}'.format(prop_name), self._hdl_g_obj_notify)

    def _getter(self) -> Any:
        return self._g_obj.get_property(self._prop_name)

    def _setter(self, value: Any) -> None:
        self._g_obj.handler_block(self._hdl_g_obj_notify_id)
        self._g_obj.set_property(self._prop_name, value)
        self._g_obj.handler_unblock(self._hdl_g_obj_notify_id)

    def _hdl_g_obj_notify(self, g_obj: GObject.Object, pspec: GObject.GParamSpec) -> None:
        self._bn.poke()

    def unlink(self):
        if self._g_obj.handler_is_connected(self._hdl_g_obj_notify_id):
            self._g_obj.disconnect(self._hdl_g_obj_notify_id)

        self._bn.getter = None
        self._bn.setter = None


# Give the class a more 'function-y' sounding name.
link_atomic_bn_adapter_to_g_prop = AtomicBindableAdapterGPropLink
