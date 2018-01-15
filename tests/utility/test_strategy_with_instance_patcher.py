from opendrop.utility.instance_patcher import patch_instance
from opendrop.utility.strategy import strategy

MY_STRATEGY_DEF_RET = 0
MY_STRATEGY_IMP1_RET = 1
MY_STRATEGY_IMP2_RET = 2

MY_OTHER_STRATEGY_DEF_RET = 10
MY_OTHER_STRATEGY_IMP1_RET = 11
MY_OTHER_STRATEGY_IMP2_RET = 12


class A:
    @strategy
    def my_strategy(self):
        return MY_STRATEGY_DEF_RET


class APatch(A):
    @strategy
    def my_other_strategy(self):
        return MY_OTHER_STRATEGY_DEF_RET


def my_strategy_imp1(self):
    return MY_STRATEGY_IMP1_RET


def my_strategy_imp2(self):
    return MY_STRATEGY_IMP2_RET


def my_other_strategy_imp1(self):
    return MY_OTHER_STRATEGY_IMP1_RET


def my_other_strategy_imp2(self):
    return MY_OTHER_STRATEGY_IMP2_RET


def test_strategy_with_instance_patcher():
    a1 = A()
    a2 = A()

    a1_patched = patch_instance(a1, APatch)
    a2_patched = patch_instance(a2, APatch)

    A.my_strategy.use(my_strategy_imp1)

    assert a1.my_strategy() == a2.my_strategy() == a1_patched.my_strategy() == a2_patched.my_strategy() \
           == MY_STRATEGY_IMP1_RET

    a1_patched.my_strategy.use(my_strategy_imp2)

    assert a1.my_strategy() == a1_patched.my_strategy() == MY_STRATEGY_IMP2_RET and \
           a2.my_strategy() == a2_patched.my_strategy() == MY_STRATEGY_IMP1_RET

    APatch.my_other_strategy.use(my_other_strategy_imp1)

    assert a1_patched.my_other_strategy() == a2_patched.my_other_strategy() == MY_OTHER_STRATEGY_IMP1_RET

    a1_patched.my_other_strategy.use(my_other_strategy_imp2)

    assert a1_patched.my_other_strategy() == MY_OTHER_STRATEGY_IMP2_RET and \
           a2_patched.my_other_strategy() == MY_OTHER_STRATEGY_IMP1_RET
