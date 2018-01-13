from pytest import raises

from opendrop.utility.instance_patcher import patch_instance


class A:
    def __init__(self, v):
        self.val = v
        self._prop = 0

    def a_func(self, v):
        return v

    def dothis(self, v):
        return v

    def set_val(self, v):
        self.val = v

    @classmethod
    def cls_method(cls):
        return cls

    @property
    def prop(self):
        return self._prop

    print('1', prop)

    @prop.setter
    def prop(self, v):
        print('A prop')
        self._prop = v

    print('2', prop)

    def __add__(self, other):
        return 9

    def __mul__(self, other):
        return 3


class A2(A):
    def dothis(self, v):
        return 2 * v

    def dothis2(self, v):
        self.a = v

    def a2_func(self, v):
        return 2 * v

    def set_val(self, v):
        self.val = 3 * v

    @A.prop.setter
    def prop(self, v):
        print('A2 prop')
        self._prop = 10 * v

    def __add__(self, other):
        return 99


class TestPatchedInstance:
    def setup(self):
        self.a = A(0)
        self.a_patched = patch_instance(self.a, A2)

    def test_method_resolution(self):
        assert self.a.dothis(5) == A.dothis(self.a, 5)
        assert self.a_patched.dothis(5) == A2.dothis(self.a_patched, 5)

        assert self.a.a_func(1) == self.a_patched.a_func(1)

        assert self.a_patched.a2_func(1) == 2

        with raises(AttributeError):
            self.a.a2_func(1)

    def test_attribute_access(self):
        o = object()

        self.a.val = o

        assert self.a.val == self.a_patched.val == o

    def test_method_self_parameter(self):
        self.a_patched.set_val(5)

        assert self.a.val == self.a_patched.val == 3 * 5

    def test_property(self):
        self.a.prop = 1

        assert self.a.prop == self.a_patched.prop == 1

        self.a_patched.prop = 10

        assert self.a.prop == self.a_patched.prop == 10 * 10

    def test_class_method(self):
        assert self.a.cls_method() == A
        assert self.a_patched.cls_method() == A2

    def test_dunder(self):
        assert self.a + self.a == 9
        assert self.a_patched + self.a == 99
        assert self.a_patched + self.a_patched == 99

        assert self.a * self.a == 3
        assert self.a_patched * self.a == 3
        assert self.a_patched * self.a_patched == 3

        print(self.a, self.a_patched)
