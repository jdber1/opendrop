import pytest
import os

def run_all_pytest():
    # 项目根目录
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # 指定测试目录（你可以自定义）
    test_target = os.path.join(root_dir, "modules")

    # 运行 pytest，添加参数可自定义行为
    result = pytest.main([
        "-v",                    # 显示详细信息
        "--tb=short",            # 简洁 traceback
        test_target              # 要测试的路径
    ])

    return result

if __name__ == "__main__":
    raise SystemExit(run_all_pytest())
