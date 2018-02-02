import weakref

import gc
from unittest.mock import patch

from collections import defaultdict
from pytest import raises

from opendrop.utility import data_binding
from opendrop.utility.data_binding import poke
from opendrop.utility.events import HasEvents, EventSource


def test_stub(): pass


class Common(HasEvents):
    def __init__(self):
        self.events = EventSource()

        self._var0 = self.MY_VAR0
        self._var1 = self.MY_VAR1

        self.var0_setter_count = 0
        self.var1_setter_count = 0
        self.var2_deleter_count = 0

        self.var0_setter_hook = None
        self.var1_setter_hook = None

    @data_binding.property
    def var0(self):
        return self._var0

    @var0.setter
    def var0(self, v):
        if self.var0_setter_hook is not None:
            self.var0_setter_hook.__get__(self, type(self))(v)

        self.var0_setter_count += 1
        self._var0 = v

    @data_binding.property
    def var1(self):
        return self._var1

    @var1.setter
    def var1(self, v):
        if self.var1_setter_hook is not None:
            self.var1_setter_hook.__get__(self, type(self))(v)

        self.var1_setter_count += 1
        self._var1 = v

    @data_binding.property
    def var2(self):
        return None

    @var2.deleter
    def var2(self):
        self.var2_deleter_count += 1

    @property
    def untouched(self):
        return self.var0 == self.MY_VAR0 and self.var1 == self.MY_VAR1


class Master(Common):
    MY_VAR0 = 10
    MY_VAR1 = 20


class Child(Common):
    MY_VAR0 = 1
    MY_VAR1 = 2


class TestBinder:
    def setup(self):
        self.master = Master()
        self.child = Child()

    def test_weak_ref_to_objs(self):
        binder = data_binding.Binder(self.master, self.child, routes=[])

        master_wr = weakref.ref(self.master)
        child_wr = weakref.ref(self.child)

        self.master = None
        gc.collect()

        assert master_wr() is None and child_wr() is not None

        self.child = None
        gc.collect()

        assert child_wr() is None

    def test_objs_have_strong_ref(self):
        binder_wr = weakref.ref(data_binding.Binder(self.master, self.child, routes=[]))
        gc.collect()

        assert binder_wr() is not None

    def test_auto_cleanup_when_one_obj_dies(self):
        binder_wr = weakref.ref(data_binding.Binder(self.master, self.child, routes=[]))

        del self.master
        gc.collect()

        assert binder_wr() is None

    def test_behaviour_when_del_obj_a(self):
        routes = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0)
        ]

        data_binding.Binder(self.master, self.child, routes=routes)

        self.master.var0 = 5

        assert self.master.var0 == self.child.var0 == 5

        del self.child
        gc.collect()

        # Make sure when we set `self.master.var0` now, Binder won't raise any exceptions from trying to set
        # `self.child.var0`.
        self.master.var0 = 6

        assert self.master.var0 == 6

    def test_behaviour_when_del_obj_b(self):
        # Same thing but delete obj_b
        routes = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0)
        ]

        data_binding.Binder(self.master, self.child, routes=routes)

        self.child.var0 = 5

        assert self.child.var0 == self.master.var0 == 5

        del self.master
        gc.collect()

        self.child.var0 = 6
        assert self.child.var0 == 6

    def test_unbind(self):
        routes = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0),
        ]

        binder = data_binding.Binder(self.master, self.child, routes=routes)

        self.master.var0 = 5

        assert self.master.var0 == self.child.var0 == 5

        binder.unbind()

        self.master.var0 = 6

        assert self.master.var0 == 6 and self.child.var0 == 5

    def test_dead(self):
        binder = data_binding.Binder(self.master, self.child, routes=[])

        assert not binder.dead

        binder.unbind()

        assert binder.dead

    def test_bind_with_one_way_route(self):
        routes = [
            data_binding.Route.a_to_b(prop_a=Master.var0, prop_b=Child.var0),
            data_binding.Route.b_to_a(prop_a=Master.var1, prop_b=Child.var1)
        ]

        data_binding.Binder(self.master, self.child, routes=routes)
        assert self.master.untouched and self.child.untouched

        self.master.var0 = 5

        assert self.master.var0 == self.child.var0 == 5

        self.master.var1 = 6

        assert self.master.var1 == 6 and self.child.var1 == Child.MY_VAR1

        self.child.var1 = 7

        assert self.master.var1 == self.child.var1 == 7

    def test_bind_both_ways(self):
        routes = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0),
        ]

        binder = data_binding.Binder(self.master, self.child, routes=routes)

        poke(self.master)

        self.master.var0 = 5

        assert self.master.var0 == self.child.var0 == 5

        self.child.var0 = 6

        assert self.master.var0 == self.child.var0 == 6

    def test_bind_variables_with_different_names(self):
        routes = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var1),
            *data_binding.Route.both(prop_a=Master.var1, prop_b=Child.var0),
        ]

        binder = data_binding.Binder(self.master, self.child, routes=routes)

        poke(self.master)

        assert self.master.var0 == self.child.var1
        assert self.master.var1 == self.child.var0

    def test_chained_binds(self):
        # Diagram:
        #
        #     master -- child -- other_child
        #
        routes1 = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0)
        ]

        routes2 = [
            *data_binding.Route.both(prop_a=Child.var0, prop_b=Child.var0)
        ]

        other_child = Child()

        data_binding.Binder(self.master, self.child, routes=routes1)
        data_binding.Binder(self.child, other_child, routes=routes2)

        def assert_var0_setter_count_less_than_one(self, v):
            assert self.var0_setter_count < 1

        # Make sure the var0 setters of each instance aren't called more than once
        self.master.var0_setter_hook = assert_var0_setter_count_less_than_one
        self.child.var0_setter_hook  = assert_var0_setter_count_less_than_one
        other_child.var0_setter_hook = assert_var0_setter_count_less_than_one

        self.master.var0 = 99

        assert self.master.var0 == self.child.var0 == other_child.var0 == 99

    def test_circular_chained_bind(self):
        # Diagram:
        #
        #     master -- child -- other_child
        #                  \         /
        #                 another_child
        #
        routes1 = [
            *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0)
        ]

        routes2 = [
            *data_binding.Route.both(prop_a=Child.var0, prop_b=Child.var0)
        ]

        other_child = Child()
        another_child = Child()

        data_binding.Binder(self.master, self.child, routes=routes1)
        data_binding.Binder(self.child, other_child, routes=routes2)
        data_binding.Binder(other_child, another_child, routes=routes2)
        data_binding.Binder(another_child, self.child, routes=routes2)

        def assert_var0_setter_count_less_than_one(self, v):
            assert self.var0_setter_count < 1

        self.master.var0_setter_hook   = assert_var0_setter_count_less_than_one
        self.child.var0_setter_hook    = assert_var0_setter_count_less_than_one
        other_child.var0_setter_hook   = assert_var0_setter_count_less_than_one
        another_child.var0_setter_hook = assert_var0_setter_count_less_than_one

        self.master.var0 = 99

        assert self.master.var0 == self.child.var0 == other_child.var0 == another_child.var0 == 99

    def test_modify_routes_after_instantiation(self):
        routes = [
            data_binding.Route.a_to_b(prop_a=Master.var0, prop_b=Child.var0)
        ]

        data_binding.Binder(self.master, self.child, routes=routes)

        self.master.var0 = 5

        assert self.master.var0 == self.child.var0

        self.child.var0 = 6

        assert self.master.var0 == 5 and self.child.var0 == 6

        routes.append(
            data_binding.Route.b_to_a(prop_a=Master.var0, prop_b=Child.var0)
        )

        self.child.var0 = 7

        assert self.master.var0 == self.child.var0 == 7

    def test_bind_same_objs(self):
        with raises(ValueError):
            data_binding.Binder(self.master, self.master, routes=[])


# Test data_binding2.property
def test_property_overriding_behaviour():
    child = Child()

    child.var0 = 10

    assert child.var0 == child._var0 == 10

    class Subchild(Child):
        @Child.var0.getter
        def var0(self):
            return 2 * self._var0

        @var0.setter
        def var0(self, v):
            self._var0 = 2 * v

    subchild = Subchild()

    child.var0 = 10
    subchild.var0 = 10

    assert child.var0 == 10
    assert subchild.var0 == 40

def test_property_deleter():
    child = Child()

    del child.var2

    assert child.var2_deleter_count == 1


# Test poke
def test_poke_single_property():
    routes = [
        *data_binding.Route.both(prop_a=Master.var0, prop_b=Child.var0),
        *data_binding.Route.both(prop_a=Master.var1, prop_b=Child.var1)
    ]

    master = Master()
    child = Child()

    data_binding.Binder(master, child, routes=routes)

    assert master.untouched and child.untouched

    poke(master, Master.var0)

    assert master.var0 == child.var0 == master.MY_VAR0
    assert master.var1 == Master.MY_VAR1 and child.var1 == child.MY_VAR1


def test_poke_all_properties():
    routes = [
        data_binding.Route.b_to_a(prop_a=Master.var0, prop_b=Child.var0),
        data_binding.Route.b_to_a(prop_a=Master.var1, prop_b=Child.var1)
    ]

    master = Master()
    child = Child()

    data_binding.Binder(master, child, routes=routes)

    assert master.untouched and child.untouched

    poke(child)

    assert master.var0 == child.var0 == child.MY_VAR0
    assert master.var1 == child.var1 == child.MY_VAR1


def test_poke_nonexistent_property():
    master = Master()

    mythical_prop = data_binding.property(lambda self: 0)

    with raises(ValueError):
        poke(master, mythical_prop)


# Test misc
def test_bind_alias():
    assert data_binding.bind == data_binding.Binder