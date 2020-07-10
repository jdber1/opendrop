from typing import Sequence, Type, TypeVar, Callable
from gi.repository import Gtk

from ._template import mark_as_templated
from ._injector import mark_as_injection_container

WidgetClassT = TypeVar('WidgetClassT', bound=Type[Gtk.Widget])


def componentclass(
        template_path: str = '',
        modules: Sequence = (),
        auto_bind: bool = True,
) -> Callable[[WidgetClassT], WidgetClassT]:
    def wrapper(widget_class: WidgetClassT) -> WidgetClassT:
        mark_as_injection_container(widget_class, modules, auto_bind)

        if template_path:
            mark_as_templated(widget_class, template_path)

        return widget_class

    return wrapper
