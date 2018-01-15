from typing import TypeVar, Type, Any

T = TypeVar('T')
U = TypeVar('U')


# Limitations: type.__set/getattribute__ won't work correctly on PatchedInstance classes:
#
#     class A:
#         pass
#
#     class APatch:
#         @classmethod
#         def test(cls):
#             type.__setattr__(cls, 'test', 10)
#
#     a = A()
#     a_patched = patch_instance(a)
#
#     a_patched.test()
#
#     print(type.__getattribute__(type(a_patched), 'test'))  # 10
#     print(type.__getattribute__(A, 'test'))                # AttributeError: type object 'A' has no attribute 'temp'
#     print(type(a_patched).test)                            # AttributeError: type object 'A' has no attribute 'temp'
#     print(A.test)                                          # AttributeError: type object 'A' has no attribute 'temp'
#
# Instances (and classes) of PatchedInstance also won't equal the original instance/class:
#
#     a = A()
#     a_patched = patch_instance(a)
#
#     print(a == a_patched)  # False
#     print(A == type(a_patched))  # False
#
# They may also have a different hash unless a __hash__ is implemented in a way that makes them equal.
#
# PatchedInstance instances are implemented by setting the __dict__ attribute of the patched instance to that of the
# source instance. The patched instances' class (i.e. `type(patched_instance)`) has a metaclass overriding
# __getattribute__ and __setattr__ for redirecting attribute accesses to the source instance class, this is not a
# completely transparent process but will behave as expected for most usecases. The source instance class and mixin
# class's metaclass __getattribute__ and __setattr__ are ignored as a byproduct of this implementation. Also, attribute
# access to the metaclass of a patched instance are not redirected to the metaclass of the source instance, and neither
# are the metaclasses of metaclasses.
#
# Basically, attribute access works for patched instances, works most of the time
# for classes of patched instances, and do not work for its metaclasses or metaclasses of metaclasses)

def patch_instance(source: T, mixin: Type[U]) -> U:
    source_cls = type(source)  # type: Type[T]

    inherit = type(mixin), type(source_cls)

    if inherit[0] == inherit[1]:
        inherit = (inherit[0],)
    elif issubclass(type(source_cls), type(mixin)):
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
