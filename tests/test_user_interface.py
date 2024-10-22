import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import sys
import os


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

        
        self.ui = UserInterface(None)

    def tearDown(self):
        
        pass

    def test_create_title(self):
        
        self.ui.create_title()
        self.assertTrue(self.ui.root.title.called)

    @patch('modules.user_interface.tk.StringVar')
    def test_create_user_inputs(self, MockStringVar):
        
        self.ui.create_user_inputs()
        self.assertIsNotNone(self.ui.drop_ID_method)
        self.assertIsNotNone(self.ui.threshold_method)
        self.assertIsNotNone(self.ui.density_outer)

    def test_validate_float_valid(self):
        
        result = self.ui.validate_float('1', '1', '123.45', '', '5', 'key', 'focusout', 'test_widget')
        self.assertTrue(result)

    def test_validate_float_invalid(self):
        
        result = self.ui.validate_float('1', '1', '123.abc', '', '5', 'key', 'focusout', 'test_widget')
        self.assertFalse(result)

    def test_validate_int_valid(self):
        
        result = self.ui.validate_int('1', '1', '123', '', '5', 'key', 'focusout', 'test_widget')
        self.assertTrue(result)

    def test_validate_int_invalid(self):
        
        result = self.ui.validate_int('1', '1', '123abc', '', '5', 'key', 'focusout', 'test_widget')
        self.assertFalse(result)

    @patch('modules.user_interface.tkFileDialog.askopenfilenames', return_value=['file1.jpg', 'file2.jpg'])  
    @patch('modules.user_interface.sys.exit')  
    @patch('modules.user_interface.UserInterface.export_parameters')
    @patch('modules.user_interface.UserInterface.update_user_settings')
    def test_run(self, mock_update, mock_export, mock_exit, mock_askopenfilenames):
        
        mock_data = MagicMock()
        mock_data.number_of_frames = 2

        
        self.ui.image_source.get_value = MagicMock(return_value='Local images')

        
        self.ui.run(mock_data)

        
        self.assertEqual(mock_data.import_files, ['file1.jpg', 'file2.jpg'])

        
        mock_askopenfilenames.assert_called_once()

        
        mock_exit.assert_not_called()




    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_export_parameters(self, mock_file):
        
        self.ui.PATH_TO_FILE = "E:\\conan-ml-main\\modules\\parameters.csv"  
        self.ui.export_parameters()
        mock_file.assert_called_once_with(self.ui.PATH_TO_FILE, 'w')


if __name__ == '__main__':
    unittest.main()

