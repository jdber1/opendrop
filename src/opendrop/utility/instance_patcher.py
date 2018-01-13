from typing import TypeVar, Type, Any

T = TypeVar('T')
U = TypeVar('U')


# Limitations: object.__set/getattribute__ won't work correctly on a PatchedInstance, PatchedInstance's also won't equal
# the instance that was patched, and may have a different hash unless a __hash__ is implemented in a way that makes them
# equal.
def patch_instance(source: T, mixin: Type[U]) -> U:
    class PatchedInstance(mixin):
        def __new__(cls, *args, **kwargs):
            return object.__new__(cls)

        def __init__(self):
            pass

        def __getattribute__(self, name: str) -> Any:
            try:
                attr = getattr(mixin, name)

                if hasattr(attr, '__get__'):
                    if hasattr(attr, '__set__') or name not in source.__dict__:
                        attr = attr.__get__(self, mixin)
                    else:
                        return source.__dict__[name]

                return attr
            except AttributeError:
                return getattr(source, name)

        def __setattr__(self, name: str, value: Any) -> None:
            try:
                attr = getattr(mixin, name)

                if hasattr(attr, '__set__'):
                    attr.__set__(self, value)
                else:
                    raise AttributeError
            except AttributeError:
                return setattr(source, name, value)

    return PatchedInstance()
