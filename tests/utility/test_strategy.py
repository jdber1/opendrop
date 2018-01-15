import pytest
from pytest import raises

from opendrop.utility.strategy import strategy

def test_stub(): ...


@pytest.mark.skip
def test_positional_only_impl():
    @strategy
    def my_hook(a, b):
        return 0

    with raises(ValueError):
        my_hook.use(pow)

@pytest.mark.skip
class TestStrategy:
    def setup(self):
        @strategy
        def my_hook(a, b, c, *, e=0):
            return 0

        def my_impl(a, b, c):
            return a + b + c

        def my_impl2(a, b, c, d=1, e=10, f=100):
            return a + b + c + d + e

        self.my_hook = my_hook
        self.my_impl = my_impl
        self.my_impl2 = my_impl2

    def test_default(self):
        assert self.my_hook(1, 2, 3) == 0

    def test_use(self):
        self.my_hook.use(self.my_impl)

        assert self.my_hook(1, 2, 3) == self.my_impl(1, 2, 3)

    def test_clear(self):
        assert self.my_hook(1, 2, 3) == 0

        self.my_hook.use(self.my_impl)

        assert self.my_hook(1, 2, 3) == self.my_impl(1, 2, 3)

        self.my_hook.clear()

        assert self.my_hook(1, 2, 3) == 0

    @pytest.mark.skip
    def test_use_wrong_signature(self):
        def my_wrong_impl(a, b, c, d): pass

        with raises(ValueError):
            self.my_hook.use(my_wrong_impl)

        def my_wrong_impl2(x, y, z): pass

        with raises(ValueError):
            self.my_hook.use(my_wrong_impl2)

    @pytest.mark.skip
    def test_use_compatible(self):
        self.my_hook.use(self.my_impl2)

        assert self.my_hook(1, 2, 3) == self.my_impl2(1, 2, 3)


class TestBoundStrategy:
    def setup(self):
        class A:
            @strategy
            def my_hook1(self, a, b, c):
                return self, 0

            @strategy
            @classmethod
            def my_hook2(cls, a, b, c):
                return cls, 0

            @strategy
            @staticmethod
            def my_hook3(a, b, c):
                return None, 0

        def my_impl1(self, a, b, c):
            return self, a + b + c

        def my_impl2(self, a, b, c):
            return self, 2 * (a+b+c)

        def my_impl3(a, b, c):
            return None, 3 * (a+b+c)

        class B(A):
            pass

        self.A = A
        self.B = B

        self.my_impl1 = my_impl1
        self.my_impl2 = my_impl2
        self.my_impl3 = my_impl3

    def test_default(self):
        a = self.A()

        lret, rret = a.my_hook1(1, 2, 3)

        assert lret == a and rret == 0

    def test_use(self):
        a1 = self.A()
        a2 = self.A()

        a1.my_hook1.use(self.my_impl1)
        a2.my_hook1.use(self.my_impl2)

        lret1, rret1 = a1.my_hook1(1, 2, 3)
        lret2, rret2 = a2.my_hook1(1, 2, 3)

        assert lret1 == a1 and rret1 == 6
        assert lret2 == a2 and rret2 == 12

    def test_use_on_class_strategy(self):
        A = self.A
        a = self.A()

        A.my_hook1.use(self.my_impl1)

        assert a.my_hook1(1, 2, 3) == self.my_impl1(a, 1, 2, 3)

    def test_classmethod_strategy(self):
        A = self.A
        a = self.A()

        A.my_hook2.use(self.my_impl2)

        assert A.my_hook2(1, 2, 3) == a.my_hook2(1, 2, 3) == self.my_impl2(A, 1, 2, 3)

    def test_staticmethod_strategy(self):
        A = self.A
        a = self.A()

        A.my_hook3.use(self.my_impl3)

        lret1, rret1 = A.my_hook3(1, 2, 3)
        lret2, rret2 = a.my_hook3(1, 2, 3)

        assert A.my_hook3(1, 2, 3) == a.my_hook3(1, 2, 3) == self.my_impl3(1, 2, 3)

    @pytest.mark.skip
    def test_use_wrong_signature(self):
        with raises(ValueError):
            self.A.my_hook1.use(self.my_impl3)

    def test_inherited_classmethod_strategy(self):
        f_a = self.A.my_hook2
        f_b = self.B.my_hook2

        assert f_a(0, 0, 0)[0] == self.A and f_b(0, 0, 0)[0] == self.B
