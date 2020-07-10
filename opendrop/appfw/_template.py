from typing import Type, TypeVar, Callable, Any, Optional, Generic, overload
import sys
from gi.repository import Gtk, GObject, Gio

T = TypeVar('T')

WidgetClassT = TypeVar('WidgetClassT', bound=Type[Gtk.Widget])
WidgetT = TypeVar('WidgetT', bound=Gtk.Widget)


def templated(path: str) -> Callable[[WidgetClassT], WidgetClassT]:
    def wrapper(widget_class: WidgetClassT) -> WidgetClassT:
        mark_as_templated(widget_class, template_path=path)
        return widget_class

    return wrapper


def mark_as_templated(widget_class: WidgetClassT, template_path: str) -> WidgetClassT:
    # If resource name is not an absolute path, we use some tricks to resolve it.
    if not template_path.startswith('/'):
        package_name = get_owner_package(widget_class)
        if package_name is None:
            raise RuntimeError(
                "Could not determine the owner package of '{}' to resolve relative template path"
                .format(widget_class.__name__)
            )

        template_path = resolve_relative_resource(package_name, template_path)

    template = Gio.resources_lookup_data(template_path, Gio.ResourceLookupFlags.NONE).get_data().decode()

    widget_class.__widget_template__ = TemplateSpec(template, widget_class.__init__)

    # Hacky.., override with our own __init__ function.
    widget_class.__init__ = override_init

    return widget_class


class TemplateSpec:
    def __init__(self, template: str, original_init: Callable) -> None:
        self.template = template
        self.original_init = original_init


class TemplatePrivate:
    private_key = '_template_private_data'

    def __init__(self, builder: Gtk.Builder) -> None:
        self.builder = builder
        self.child_cache = {}

    def install(self, target: Any) -> None:
        target.__dict__[__class__.private_key] = self

    @staticmethod
    def get(owner: Any) -> 'TemplatePrivate':
        return owner.__dict__[__class__.private_key]


def override_init(self, *args, **kwargs) -> None:
    template_spec = self.__widget_template__

    # Invoke original __init__ function
    template_spec.original_init(self, *args, **kwargs)

    # Build template
    template = template_spec.template

    builder = Gtk.Builder()
    builder.extend_with_template(self, type(self), template, len(template))

    private = TemplatePrivate(builder)
    private.install(self)

    # Connect callbacks
    builder.connect_signals_full(builder_connect_helper, self)

    after_template_init = getattr(self, 'after_template_init', None)
    if after_template_init:
        after_template_init()


def builder_connect_helper(
        builder: Gtk.Builder,
        obj: GObject.Object,
        signal_name: str,
        handler_name: str,
        connect_obj: Optional[GObject.Object],
        flags: GObject.ConnectFlags,
        component: Gtk.Widget,
) -> None:
    if flags & GObject.ConnectFlags.SWAPPED:
        raise ValueError(
            "{!r} not supported"
            .format(GObject.ConnectFlags.SWAPPED)
        )

    handler = getattr(component, handler_name)
    args = ()

    if connect_obj:
        # Special case handling of connect_obj with g_signal_connect_object() is not needed (and not
        # implemented anyway) in python.
        args = (connect_obj,)

    if flags & GObject.ConnectFlags.AFTER:
        obj.connect_after(signal_name, handler, *args)
    else:
        obj.connect(signal_name, handler, *args)


def get_owner_package(class_like: Any) -> Optional[str]:
    module_name = class_like.__module__
    if not module_name:
        return None

    try:
        module = sys.modules[module_name]
    except KeyError:
        return None

    package_name = module.__package__
    if not package_name:
        return None

    return package_name


def resolve_relative_resource(package: str, path: str) -> str:
    if path.startswith('/'):
        return path

    abspath_parts = tuple(package.split('.'))

    for path_part in path.split('/'):
        if path_part == '':
            continue
        elif path_part == '.':
            continue
        elif path_part == '..':
            if len(abspath_parts) == 0:
                raise FileNotFoundError
            abspath_parts = abspath_parts[:-1]
        else:
            abspath_parts = abspath_parts + (path_part,)

    abspath = '/' + '/'.join(abspath_parts)

    return abspath


class TemplateChild(Generic[WidgetT]):
    def __init__(self, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, instance) -> WidgetT: ...
    @overload
    def __get__(self: T, instance, owner) -> T: ...

    def __get__(self, instance, owner=None):
        if owner is None:
            return self

        template_priv = TemplatePrivate.get(instance)

        if self._name not in template_priv.child_cache:
            template_priv.child_cache[self._name] = template_priv.builder.get_object(self._name)

        return template_priv.child_cache[self._name]
