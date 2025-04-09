from typing import Any, Generic, TypeVar, Type, overload, Literal
import xml.etree.ElementTree as ET
from gi.repository import Gtk, GObject


T = TypeVar('T')
U = TypeVar('U')


class TemplateInfo:
    def __init__(self, data: str) -> None:
        self.data = data
        xml = ET.fromstring(data)

        name = None
        parent = None
        for e in xml.iter('template'):
            name = e.get('class')
            parent = e.get('parent')
            break

        if name is None or parent is None:
            raise ValueError("Template tag is missing 'class' or 'parent' attribute")

        self.name = name
        self.parent = GObject.type_from_name(parent).pytype


class TemplateChild(Generic[T]):
    def __init__(self, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, instance, owner) -> T: ...
    @overload
    def __get__(self: U, instance: Literal[None], owner) -> U: ...

    def __get__(self, instance, owner=None):
        if owner is None:
            return self

        template_priv = TemplatePrivate.get(instance)

        if self._name not in template_priv.child_cache:
            template_priv.child_cache[self._name] = template_priv.builder.get_object(self._name)

        return template_priv.child_cache[self._name]


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
