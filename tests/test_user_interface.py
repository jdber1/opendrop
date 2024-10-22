import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import sys
import os

# 手动将项目的根目录添加到 sys.path 中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.user_interface import *

class TestUserInterface(unittest.TestCase):

    @patch('tkinter.Tk')
    @patch('modules.user_interface.tk.StringVar')
    @patch('modules.user_interface.tk.IntVar')
    @patch('sys.exit')
    def setUp(self, MockExit, MockIntVar, MockStringVar, MockTk):
        # Mock the root tkinter window to avoid creating an actual GUI
        self.root = MockTk()

        # 创建 UserInterface 对象，并传入一个 mock 数据
        self.ui = UserInterface(None)

    def tearDown(self):
        # 停止 patch 以清理 mock 对象
        pass

    def test_create_title(self):
        # 测试是否正确创建标题
        self.ui.create_title()
        self.assertTrue(self.ui.root.title.called)

    @patch('modules.user_interface.tk.StringVar')
    def test_create_user_inputs(self, MockStringVar):
        # 测试是否正确创建用户输入项
        self.ui.create_user_inputs()
        self.assertIsNotNone(self.ui.drop_ID_method)
        self.assertIsNotNone(self.ui.threshold_method)
        self.assertIsNotNone(self.ui.density_outer)

    def test_validate_float_valid(self):
        # 测试浮点数校验函数，输入合法值
        result = self.ui.validate_float('1', '1', '123.45', '', '5', 'key', 'focusout', 'test_widget')
        self.assertTrue(result)

    def test_validate_float_invalid(self):
        # 测试浮点数校验函数，输入非法值
        result = self.ui.validate_float('1', '1', '123.abc', '', '5', 'key', 'focusout', 'test_widget')
        self.assertFalse(result)

    def test_validate_int_valid(self):
        # 测试整数校验函数，输入合法值
        result = self.ui.validate_int('1', '1', '123', '', '5', 'key', 'focusout', 'test_widget')
        self.assertTrue(result)

    def test_validate_int_invalid(self):
        # 测试整数校验函数，输入非法值
        result = self.ui.validate_int('1', '1', '123abc', '', '5', 'key', 'focusout', 'test_widget')
        self.assertFalse(result)

    @patch('modules.user_interface.tkFileDialog.askopenfilenames', return_value=['file1.jpg', 'file2.jpg'])  # 模拟文件选择对话框
    @patch('modules.user_interface.sys.exit')  # 模拟 sys.exit 防止它退出测试
    @patch('modules.user_interface.UserInterface.export_parameters')
    @patch('modules.user_interface.UserInterface.update_user_settings')
    def test_run(self, mock_update, mock_export, mock_exit, mock_askopenfilenames):
        # 模拟 user_input_data
        mock_data = MagicMock()
        mock_data.number_of_frames = 2

        # 模拟 image_source 返回 'Local images'
        self.ui.image_source.get_value = MagicMock(return_value='Local images')

        # 执行 run 方法
        self.ui.run(mock_data)

        # 检查 import_files 是否设置为模拟的文件列表
        self.assertEqual(mock_data.import_files, ['file1.jpg', 'file2.jpg'])

        # 检查 import_files 被正确调用
        mock_askopenfilenames.assert_called_once()

        # 确保没有调用 sys.exit
        mock_exit.assert_not_called()




    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_export_parameters(self, mock_file):
        # 修正并测试导出参数的功能
        self.ui.PATH_TO_FILE = "E:\\conan-ml-main\\modules\\parameters.csv"  # 使用实际路径
        self.ui.export_parameters()
        mock_file.assert_called_once_with(self.ui.PATH_TO_FILE, 'w')


if __name__ == '__main__':
    unittest.main()

