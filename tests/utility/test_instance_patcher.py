from pytest import raises

from opendrop.utility.instance_patcher import patch_instance


class AMeta(type):
    @property
    def cls_prop(self):
        return 5


class A(metaclass=AMeta):
    cls_val = None

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
    def set_cls_val(cls, v):
        cls.cls_val = v

    @property
    def prop(self):
        return self._prop

    @prop.setter
    def prop(self, v):
        print('A prop')
        self._prop = v

    def __add__(self, other):
        return 9

    def __mul__(self, other):
        return 3


class A2:
    def dothis(self, v):
        return 2 * v

    def dothis2(self, v):
        self.a = v

    def a2_func(self, v):
        return 2 * v

    def set_val(self, v):
        self.val = 3 * v

    @classmethod
    def set_cls_val(cls, v):
        cls.cls_val = 3 * v

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

    def test_class_attribute_access(self):
        o = object()

        type(self.a_patched).cls_val = o

        assert A.cls_val == type(self.a_patched).cls_val == o

    def test_method_self_parameter(self):
        self.a_patched.set_val(5)

        assert self.a.val == self.a_patched.val == 3 * 5

    def test_class_method_self_parameter(self):
        self.a_patched.set_cls_val(5)

        assert A.cls_val == type(self.a_patched).cls_val == 3 * 5

    def test_property(self):
        self.a.prop = 1

        assert self.a.prop == self.a_patched.prop == 1

        self.a_patched.prop = 10

        assert self.a.prop == self.a_patched.prop == 10 * 10

    def test_class_property(self):
        assert type(self.a_patched).cls_prop == 5

    def test_dunder(self):
        assert self.a + self.a == 9
        assert self.a_patched + self.a == 99
        assert self.a_patched + self.a_patched == 99

        assert self.a * self.a == 3
        assert self.a_patched * self.a == 3
        assert self.a_patched * self.a_patched == 3

        print(self.a, self.a_patched)

    def test_object_setattr(self):
        object.__setattr__(self.a_patched, 'test_os_var', 15)

        assert self.a.test_os_var == self.a_patched.test_os_var == 15

    def test_object_getattribute(self):
        object.__setattr__(self.a_patched, 'test_og_var', 15)

        assert \
            object.__getattribute__(self.a, 'test_og_var') == object.__getattribute__(self.a_patched, 'test_og_var') == \
            self.a.test_og_var == self.a_patched.test_og_var \
            == 15

    def test_misc(self):
        print(self.a == self.a_patched)


class ANoMeta:
    pass


class A2NoMeta:
    pass


def test_patch_with_same_metaclass():
    a = ANoMeta()
    a_patched = patch_instance(a, A2NoMeta)
