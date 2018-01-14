from typing import TypeVar, Type, Any

T = TypeVar('T')
U = TypeVar('U')


# Limitations: object.__set/getattribute__ won't work correctly on a PatchedInstance, PatchedInstance's also won't equal
# the instance that was patched, and may have a different hash unless a __hash__ is implemented in a way that makes them
# equal.
def patch_instance(source: T, mixin: Type[U]) -> U:
    source_cls = type(source)  # type: Type[T]

    inherit = type(mixin), type(source_cls)

    if issubclass(type(source_cls), type(mixin)):
        inherit = reversed(inherit)

    class PatchedInstanceMeta(*inherit):
        def __getattribute__(self, name: str) -> Any:
            if name in ('__new__', '__init__'):
                return type.__getattribute__(self, name)

            try:
                attr = getattr(type(mixin), name) if hasattr(type(mixin), name) else getattr(type(source_cls), name)

                if hasattr(attr, '__get__'):
                    if hasattr(attr, '__set__') or name not in source_cls.__dict__:
                        attr = attr.__get__(self, type(source_cls))
                    else:
                        attr = source_cls.__dict__[name]

                return attr
            except AttributeError:
                return getattr(source_cls, name)

        def __setattr__(self, name: str, value: Any) -> None:
            try:
                attr = getattr(type(mixin), name) if hasattr(type(mixin), name) else getattr(type(source_cls), name)

                if hasattr(attr, '__set__'):
                    attr.__set__(self, value)
                else:
                    raise AttributeError
            except AttributeError:
                return setattr(source_cls, name, value)

    class PatchedInstance(mixin, source_cls, metaclass=PatchedInstanceMeta):
        def __new__(cls, *args, **kwargs):
            obj = object.__new__(cls)
            obj.__dict__ = source.__dict__

            return obj

        def __init__(self):
            pass

    return PatchedInstance()
