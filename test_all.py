import unittest
import os

def run_all_tests():
    # 找到 tests 目录
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')

    # 自动发现所有以 test_ 开头的 Python 测试文件
    suite = unittest.defaultTestLoader.discover(test_dir, pattern='test_*.py')

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_all_tests()