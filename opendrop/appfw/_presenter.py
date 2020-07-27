from typing import Any, Generic, Sequence, Mapping, TypeVar
from gi.repository import GObject, Gtk
from gi.types import GObjectMeta


WidgetT_co = TypeVar('WidgetT_co', bound=Gtk.Widget, covariant=True)


def install(x):
    tag(x, 'install', True)
    return x


def tag(x, name: str, value: Any):
    if not hasattr(x, '__component_tags__'):
        x.__component_tags__ = {}
    x.__component_tags__[name] = value


def get_tag(x, name: str) -> Any:
    if not hasattr(x, '__component_tags__'):
        return None
    else:
        try:
            return x.__component_tags__[name]
        except KeyError:
            return None


class PresenterMeta(GObjectMeta, type(Generic)):
    def __new__(cls, name: str, bases: Sequence, namespace: Mapping[str, Any], **kwargs) -> 'PresenterMeta':
        install_methods = {}
        install_props = {}
        install_signals = {}
        for n, v in namespace.items():
            if not get_tag(v, 'install'): continue

            if isinstance(v, GObject.Property):
                install_props[n.replace('_', '-')] = v
            elif isinstance(v, GObject.Signal):
                install_signals[n.replace('_', '-')] = v
            elif callable(v):
                install_methods[n] = v
            else:
                raise ValueError(
                    "Can only install functions, properties, or signals, got '{}'"
                    .format(v)
                )

        namespace = {
            **namespace,
            '__install_methods__': install_methods,
            '__install_props__': install_props,
            '__install_signals__': install_signals,
        }

        return GObjectMeta.__new__(cls, name, bases, namespace, **kwargs)


class Presenter(GObject.Object, Generic[WidgetT_co], metaclass=PresenterMeta):
    def __init__(self) -> None:
        # Manually initialise GObject.Object later.
        pass

    @property
    def host(self) -> WidgetT_co:
        return self.__host

    @host.setter
    def host(self, host: WidgetT_co) -> None:
        try:
            self.__host
        except AttributeError:
            self.__host = host
        else:
            raise ValueError("Host already set")

    def after_view_init(self) -> None:
        pass
