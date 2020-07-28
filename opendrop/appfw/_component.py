import sys
from typing import Any, Callable, Sequence, Type, TypeVar, Optional
from types import MethodType

from gi.repository import GObject, Gio, Gtk
from gi.types import GObjectMeta

from ._injector_override import Injector
from ._template import TemplateInfo, TemplatePrivate
from ._presenter import Presenter


WidgetClassT = TypeVar('WidgetClassT', bound=Type[Gtk.Widget])
PresenterClassT = TypeVar('PresenterClassT', bound=Type[Presenter])
T = TypeVar('T')


def component(
        template_path: str,
        modules: Sequence = (),
        auto_bind: bool = True
) -> Callable[[PresenterClassT], PresenterClassT]:
    def wrapper(presenter_class: PresenterClassT) -> PresenterClassT:
        register_component(presenter_class, template_path, modules, auto_bind)
        return presenter_class
    return wrapper


def register_component(
        presenter_class: Type[Presenter],
        template_path: str,
        modules: Sequence,
        auto_bind: bool
) -> None:
    # If resource name is not an absolute path, we use some tricks to resolve it.
    if not template_path.startswith('/'):
        package_name = get_owner_package(presenter_class)
        if package_name is None:
            raise RuntimeError(
                "Could not determine the owner package of '{}' to resolve relative template path"
                .format(presenter_class.__name__)
            )

        template_path = resolve_relative_resource(package_name, template_path)

    template = Gio.resources_lookup_data(template_path, Gio.ResourceLookupFlags.NONE).get_data().decode()
    component_spec = ComponentSpec(presenter_class, template, modules, auto_bind)

    template_info = TemplateInfo(template)
    host_name = template_info.name
    host_parent = template_info.parent

    install_signals = {}
    for name, signal in presenter_class.__install_signals__.items():
        args = signal.get_signal_args()
        if args[0] & GObject.SignalFlags.ACTION:
            raise ValueError("Installing action signals not supported")
        install_signals[name] = args

    install_methods = {}
    for name, func in presenter_class.__install_methods__.items():
        install_methods[name] = InstalledMethod(func)

    install_props = {}
    for name, prop in presenter_class.__install_props__.items():
        args = prop.get_pspec_args()
        flags = args[-1]
        flags |= GObject.ParamFlags.EXPLICIT_NOTIFY
        install_props[name] = args[:-1] + (flags,)

    namespace = {
        **install_methods,

        '__gtype_name__': host_name,
        '__component__': component_spec,

        '__gproperties__': install_props,
        '__gsignals__': install_signals,

        '__init__': _component_init,

        'do_get_property': _component_get_property,
        'do_set_property': _component_set_property,
    }

    host_type = GObjectMeta(host_name, (host_parent,), namespace)

    # Not really necessary, but make it explicit that creating a new GObject subclass has a side-effect that
    # registers the new class with the GLib type system.
    GObject.type_register(host_type)


class ComponentSpec:
    def __init__(
            self,
            presenter_class: Type[Presenter],
            template: str,
            modules: Sequence, auto_bind: bool
    ) -> None:
        self.presenter_class = presenter_class
        self.template = template
        self.modules = modules
        self.auto_bind = auto_bind


class InstalledMethod:
    def __init__(self, func: Callable) -> None:
        self._func = func

    def __get__(self, host, owner=None) -> None:
        if host is None: return self
        return MethodType(self._func, host._presenter)

    def __call__(self, host, *args, **kwargs) -> Any:
        return self._func(host._presenter, *args, **kwargs)


def _component_init(self, **properties) -> None:
    component_spec = self.__component__
    presenter_class = component_spec.presenter_class

    # Configure child injector.
    current_injector = Injector.current()
    injector = Injector(
        parent=current_injector,
        modules=component_spec.modules,
        auto_bind=component_spec.auto_bind
    )

    # Expose injector for debugging/testing purposes.
    self.injector = injector

    # Create presenter.
    presenter = injector.create_object(presenter_class)

    presenter_construct_only_properties = {}
    for name, value in tuple(properties.items()):
        pspec = presenter.find_property(name)
        if pspec is None: continue

        if pspec.flags & GObject.ParamFlags.CONSTRUCT_ONLY:
            presenter_construct_only_properties[name] = value
            del properties[name]

    # Initialise GObject.
    GObject.Object.__init__(presenter, **presenter_construct_only_properties)

    self._presenter = presenter

    # Initialise host.
    super(type(self), self).__init__(**properties)

    # Connect to installed properties 'notify' signals.
    for prop_name in presenter_class.__install_props__.keys():
        presenter.connect(
            'notify::{}'.format(prop_name),
            lambda *_, prop_name=prop_name: self.notify(prop_name)
        )

    # Forward installed signal emissions.
    for signal_name in presenter_class.__install_signals__.keys():
        presenter.connect_after(
            signal_name,
            lambda _, *args, signal_name=signal_name: self.emit(signal_name, *args)
        )

    presenter.host = self

    # Create template builder.
    builder = Gtk.Builder()
    builder.expose_object('@', presenter)

    # Build template.
    template = component_spec.template

    injector.call_with_injection(
        lambda *args: builder.extend_with_template(*args),
        args=(self, type(self), template, len(template))
    )

    private = TemplatePrivate(builder)
    private.install(presenter)

    # Connect callbacks
    builder.connect_signals_full(builder_connect_helper, presenter)

    # Done.
    presenter.after_view_init()


def builder_connect_helper(
        builder: Gtk.Builder,
        obj: GObject.Object,
        signal_name: str,
        handler_name: str,
        connect_obj: Optional[GObject.Object],
        flags: GObject.ConnectFlags,
        presenter: Presenter,
) -> None:
    if flags & GObject.ConnectFlags.SWAPPED:
        raise ValueError(
            "{!r} not supported"
            .format(GObject.ConnectFlags.SWAPPED)
        )

    handler = getattr(presenter, handler_name)
    args = ()

    if connect_obj:
        # Special case handling of connect_obj with g_signal_connect_object() is not needed (and not
        # implemented anyway) in python.
        args = (connect_obj,)

    if flags & GObject.ConnectFlags.AFTER:
        obj.connect_after(signal_name, handler, *args)
    else:
        obj.connect(signal_name, handler, *args)


def _component_get_property(self, pspec: GObject.ParamSpec) -> Any:
    if pspec.name in self._presenter.__install_props__.keys():
        return self._presenter.get_property(pspec.name)
    else:
        return super(type(self), self).do_get_property(pspec.name)


def _component_set_property(self, pspec: GObject.ParamSpec, value: Any) -> None:
    if pspec.flags & GObject.ParamFlags.CONSTRUCT_ONLY:
        # Property is already set.
        return

    if pspec.name in self._presenter.__install_props__.keys():
        self._presenter.set_property(pspec.name, value)
    else:
        return super(type(self), self).do_set_property(pspec, value)


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
