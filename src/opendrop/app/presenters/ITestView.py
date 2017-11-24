from abc import ABCMeta, abstractmethod


class ITestView(ABCMeta):
    @abstractmethod
    def set_test_value(self, val): pass