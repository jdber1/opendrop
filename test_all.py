import unittest
import os
import fnmatch
import importlib.util

def find_test_files(root_dir, pattern="*_test.py"):
    matches = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(dirpath, filename))
    return matches

def import_and_add_tests(test_files):
    suite = unittest.TestSuite()
    for test_file in test_files:
        module_name = os.path.splitext(os.path.basename(test_file))[0]
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Load tests from the module
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    return suite

def run_all_tests():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = find_test_files(root_dir)
    test_suite = import_and_add_tests(test_files)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)

if __name__ == "__main__":
    run_all_tests()
