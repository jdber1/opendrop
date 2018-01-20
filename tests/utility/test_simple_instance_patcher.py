import random

import pytest

from opendrop.utility.simple_instance_patcher import patch_instance


def test_patch_instance():
    class MyClass:
        def do_this(self):
            return 0

        def do_this2(self):
            return 7

        def do_my_class_thing(self):
            return 1

        @property
        def my_prop(self):
            return 5

    class MyMixin(MyClass):
        my_attr = 4

        def do_this(self):
            return 2

        def do_my_mixin_thing(self):
            return 3

        def get_self(self):
            return self

        @property
        def my_prop(self):
            return 6

    my_obj1 = MyClass()
    my_obj2 = MyClass()

    my_obj2.do_this2 = lambda: 8

    my_obj2_patched = patch_instance(my_obj2, MyMixin)


    assert my_obj1.do_this() == 0 and my_obj2_patched.do_this() == 2
    assert my_obj2_patched.do_my_class_thing() == 1 and my_obj2_patched.do_my_mixin_thing() == 3

    assert my_obj2_patched.my_attr == 4

    assert my_obj2_patched.get_self() == my_obj2

    assert my_obj1.my_prop == my_obj2_patched.my_prop == 5

    # Methods that weren't overridden by the mixin shouldn't be patched into the target instance
    assert 'do_my_class_thing' not in my_obj2_patched.__dict__

    # Mixin should only override if methods/attributes differ between the mixin class and the class of the target
    # instance
    assert my_obj2_patched.do_this2() == 8

    with pytest.raises(AttributeError):
        my_obj1.do_my_mixin_thing()
