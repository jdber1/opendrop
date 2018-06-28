import weakref
from enum import IntEnum
from typing import Callable, Any, List, Optional, Tuple

from opendrop.utility.events import Event

# Globals:

# Keep a reference to the built-in property as we will shadow it with `DataBindingProperty` later.
_property_ = property

# Notes:
#
#   Some function annotations with type `_property_` should really be `DataBindingProperty` but Pycharm gives warnings
#   about the arguments being of type `property` (when they are actually `DataBindingProperty`) and the function
#   expects `DataBindingProperty`.
#
#   All the functions in the module that needs to interact with a property of an object will take in as a parameter, the
#   'actual' property object instead of the name of the property. The rationale for this is that it simplifies a lot of
#   the code as it saves from having to look up the property a string is referring to. Referring to the actual property
#   like `MyClass.my_prop` as opposed to `'my_prop'` also makes it easier to refactor the name of properties using
#   refactoring tools.


class Route:

    """Basically a container class to tell the Binder object how to do data binding between two objects. To create a
    Route object, use the factory methods `Route.a_to_b()`, `Route.b_to_a()`, and `Route.both()` instead of
    instantiating directly.
    """

    class Flow(IntEnum):
        A_TO_B = 0
        B_TO_A = 1

    def __init__(self, flow: Flow, prop_src: _property_, prop_dst: _property_, transform: Callable[[Any], Any]):
        self.flow = flow  # type: Route.Flow

        self.prop_src = prop_src  # type: DataBindingProperty
        self.prop_dst = prop_dst  # type: DataBindingProperty

        self.transform = transform  # type: Callable[[Any], Any]

    @classmethod
    def a_to_b(cls, prop_a: _property_, prop_b: _property_, transform: Callable[[Any], Any] = lambda _: _) -> 'Route':
        """Define a route from `prop_a` of 'object a' to `prop_b` of 'object b'. Any changes made to the `prop_a`
        property of 'object a' will be forwarded to `prop_b` of 'object b' by the Binder object. If `transform` is
        specified, the new value of `prop_a` will be passed to the transform function and the return is used to set
        `prop_b` of 'object b'.
        :param prop_a: The associated property of 'object a'.
        :param prop_b: The associated property of 'object b'.
        :param transform: Optional transform function.
        :return: Route object
        """
        return cls(Route.Flow.A_TO_B, prop_src=prop_a, prop_dst=prop_b, transform=transform)

    @classmethod
    def b_to_a(cls, prop_a: _property_, prop_b: _property_, transform: Callable[[Any], Any] = lambda _: _) -> 'Route':
        """Similar to `a_to_b` except changes in `prop_b` are forwarded to `prop_a`, using the transform function if
        provided
        """
        return cls(Route.Flow.B_TO_A, prop_src=prop_b, prop_dst=prop_a, transform=transform)

    @classmethod
    def both(cls, prop_a: _property_, prop_b: _property_, to_b: Callable[[Any], Any] = lambda _: _,
             to_a: Callable[[Any], Any] = lambda _: _) -> Tuple['Route', 'Route']:
        """
        Convenience function for creating `a_to_b` and `b_to_a` routes, return a tuple of routes.

            Route.both(prop_a, prop_b, to_b, to_a) == (Route.a_to_b(prop_a, prop_b, to_b),
                                                       Route.b_to_a(prop_a, prop_b, to_a))

        The return value will need to be unpacked before adding to a list of routes, e.g.:

            routes = [
                *Route.both(prop_a, prop_b, to_b, to_a),  # Need to unpack the tuple return value
                Route.a_to_b(other_prop_a, other_prop_b, other_to_b)
            ]

        :return: Tuple of two routes
        """
        return (cls.a_to_b(prop_a, prop_b, to_b), cls.b_to_a(prop_a, prop_b, to_a))


class Bindable:
    def __init__(self):
        self._databinding_commevent = Event()


class DataBindingProperty(_property_):

    """Can be used like the built-in property class but has additional functionality to facilitate data binding used
    internally within this module.

    Classes with a `DataBindingProperty` must also implement the `HasEvents` interface, i.e. have an attribute `events`
    which is an `EventSource` object so that the property is able to fire events if the property is modified. These
    events are prefixed with some string to avoid event naming conflicts and are only connected to by handlers within
    this module.
    """

    def __set__(self, instance: Bindable, value: Any) -> None:
        self.set(instance, value)

    def set(self, instance: Bindable, value: Any, trail: Optional[List] = None) -> None:
        if trail is None:
            trail = []
        elif instance in trail:
            return

        self._rawset(instance, value)

        trail.append(instance)

        self._changed(instance, trail)

    def _rawget(self, instance: Bindable):
        return super().__get__(instance, type(instance))

    def _rawset(self, instance: Bindable, value: Any) -> None:
        super().__set__(instance, value)

    def _changed(self, instance: Bindable, existing_trail: Optional[List] = None):
        trail = existing_trail if existing_trail is not None else [instance]

        try:
            current_value = self._rawget(instance)
        except AttributeError:
            return

        instance._databinding_commevent.fire(instance, self, current_value, trail)

    @classmethod
    def write_only(cls, fset: Callable) -> 'DataBindingProperty':
        return cls(fset=fset)


class Binder:

    """Binds properties from 'object a' to properties of 'object b', following a list of routes to determine which
    properties are bound.
    """

    dead = False

    def __init__(self, obj_a: Bindable, obj_b: Bindable, routes: List[Route]) -> None:
        """Listen for changes in properties in `obj_a` and `obj_b` and if appropriate routes exist, propagate changes
        from one object to the other. `prop_a` in `Route` refers to a property in `obj_a`, and similarly with `prop_b`.
        Only property relations described by the list of routes `routes` will have any data binding behaviour. The
        `routes` list is not copied so any changes made to it (such as adding or removing routes) will alter the binding
        behaviour of `Binder`.

        Any `prop_a` or `prop_b` defined in routes that don't exist in `obj_a` or `obj_b` will be silently ignored.

        Upon initialisation, properties of `obj_b` won't be synced to `obj_a` (or vice-versa) until changes are made to
        either property, if you wan't this behaviour, call `poke(obj_a)` after initialisation of this object to
        force a 'changed' event on all the `DataBindingProperty`s of `obj_a`.

        `obj_a` and `obj_b` will hold a strong reference to `Binder` so it is not required to maintain a reference to
        it manually. `Binder` has weak references to `obj_a` and `obj_b`. When either `obj_a` or `obj_b` is garbage
        collected, `Binder` will disconnect from the other object as well, losing its strong referents and itself be
        garbage collected if no other referents exist.

        Binder also works for 'circular binds', e.g.

            A - B - C
                 \ /
                  D

        Where A is two-way bound to B on some property (say `prop0`), and so are B-C, B-D and C-D. Changes made to
        `prop0` on any instance will be propogated to the others, with the setter only being called once and no infinite
        loops.

        :param obj_a: The object owning `prop_a` in Route
        :param obj_b: The object owning `prop_b` in Route
        :param routes: The list of routes describing which properties should be bound.
        """
        if obj_a is obj_b:
            raise ValueError('`obj_a` and `obj_b` cannot both equal the same \'{}\' object.'.format(obj_a))

        self._obj_a_ref = weakref.ref(obj_a, lambda v: self._cleanup())  # type: weakref.ref
        self._obj_b_ref = weakref.ref(obj_b, lambda v: self._cleanup())  # type: weakref.ref

        self._routes = routes  # type: List[Route]

        for obj in (obj_a, obj_b):
            # Make sure the objects have a strong ref to the Binder otherwise if the Binder is unexpectedly garbage
            # collected, obj0 and obj1 will no longer be data bound.
            obj._databinding_commevent.connect(self._handle_obj_properties_changed, immediate=True, strong_ref=True)

    def unbind(self) -> None:
        """Unbind `obj_a` and `obj_b` so their properties will no longer be bound
        :return: None
        """
        self._cleanup()

    def _routes_from(self, obj: Any) -> List[Route]:
        flow = Route.Flow.A_TO_B if obj == self._obj_a else Route.Flow.B_TO_A

        return list(filter(lambda r: r.flow == flow, self._routes))

    def _find_route(self, obj: Any, prop: DataBindingProperty) -> Optional[Route]:
        return next(filter(lambda r: r.prop_src == prop, self._routes_from(obj)), None)

    def _handle_obj_properties_changed(self, obj: Bindable, prop: DataBindingProperty, value: Any, trail: List) -> None:
        other_obj = self._get_other_obj(obj)

        # `other_obj` shouldn't have been garbage collected yet, if it has, then `_cleanup()` should have been
        # called and this event handler shouldn't have been invoked. Assert that this binder object is in a consistent
        # state.
        assert other_obj is not None

        route = self._find_route(obj, prop)

        if route is None or not hasprop(other_obj, route.prop_dst):
            return

        value_transformed = route.transform(value)

        route.prop_dst.set(other_obj, value_transformed, trail)

    def _get_other_obj(self, obj: Any):
        if obj == self._obj_a:
            return self._obj_b
        else:
            return self._obj_a

    def _cleanup(self):
        if self.dead:
            return

        for obj in (self._obj_a, self._obj_b):
            if obj is None:
                continue

            obj._databinding_commevent.disconnect_by_func(self._handle_obj_properties_changed)

        self.dead = True

    @_property_
    def _obj_a(self) -> Bindable:
        return self._obj_a_ref()

    @_property_
    def _obj_b(self) -> Bindable:
        return self._obj_b_ref()


def properties_from_obj(obj: Any) -> List[DataBindingProperty]:
    """Return a list of `DataBindingProperty`s defined in the class of `obj`."""
    props = []

    for name in dir(type(obj)):
        try:
            value = getattr(type(obj), name)
        except AttributeError:
            continue

        if isinstance(value, DataBindingProperty):
            props.append(value)

    return props


def hasprop(obj: Any, prop: _property_) -> bool:
    """Return a True if `obj` has property `prop` (i.e. if `prop` is in the class defnition of `obj`), else False.
    :param obj: Object to check for ownership of `prop`.
    :param prop: Property to check for.
    :return: True if `prop` is a property of `obj`, False otherwise.
    """
    for name in dir(type(obj)):
        if getattr(type(obj), name, None) == prop:
            return True
    else:
        return False


def poke(obj: Any, prop: Optional[_property_] = None) -> None:
    """Poke `obj` on property `prop` such that the 'changed' event is manually fired, useful for syncing another
    object's properties that have just been bound with Binder or when the underlying value of the property has changed
    without invoking the setter. If `prop` is None, then all `DataBindingProperty`s of `obj` will be 'poked'.
    :param obj: The object to poke.
    :param prop: Optional, property of `obj` to poke, if None, then poke all properties
    :return: None
    """
    if prop is None:
        for p in properties_from_obj(obj):
            poke(obj, p)

        return

    if not hasprop(obj, prop):
        raise ValueError('{} has no property {}'.format(obj, prop))

    prop._changed(obj)


property = DataBindingProperty
bind = Binder
