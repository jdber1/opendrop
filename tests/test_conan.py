# Import pytest for writing unit tests and handling assertions.
import pytest

# Import time for measuring and controlling execution delays.
import time

# Import tkinter (tk) for GUI-related operations.
import tkinter as tk

# Import patch and MagicMock to mock functions and objects during testing.
from unittest.mock import patch, MagicMock
from unittest import mock

# sys and os are used to manipulate the Python path so we can import modules properly.
import sys
import os

# Append the parent directory to sys.path so Python can find modules outside the "tests" folder.
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

# Import the functions to be tested from the conan module.
# This works because we added the parent directory to sys.path earlier.
from conan import clear_screen, pause_wait_time, quit_, cheeky_pause, main


# Test the clear_screen function
def test_clear_screen():
    with patch("os.system") as mock_system:
        clear_screen()
        mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')


# Test the pause_wait_time function when elapsed time is already greater than the pause time.
def test_pause_wait_time_longer_elapsed():
    with patch("time.sleep") as mock_sleep:
        pause_wait_time(2, 1)
        mock_sleep.assert_not_called()


# Test the pause_wait_time function when elapsed time is less than the pause time.
def test_pause_wait_time_shorter_elapsed():
    with patch("time.sleep") as mock_sleep:
        pause_wait_time(1, 2)
        mock_sleep.assert_called_once_with(1)


# Test the quit_ function
def test_quit_():
    mock_root = MagicMock()
    quit_(mock_root)
    mock_root.quit.assert_called_once()


# Test the cheeky_pause function
def test_cheeky_pause():
    with patch("tkinter.Tk") as mock_tk, patch("tkinter.Button") as mock_button, patch("tkinter.Frame") as mock_frame:
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance

        cheeky_pause()

        mock_tk.assert_called_once()
        mock_frame.assert_called_once_with(mock_root)
        mock_button.assert_called_once_with(mock_frame_instance)
        mock_root.mainloop.assert_called_once()


@mock.patch('conan.call_user_input')
@mock.patch('conan.get_image')
@mock.patch('conan.set_drop_region')
@mock.patch('conan.extract_drop_profile')
@mock.patch('conan.set_surface_line')
@mock.patch('conan.perform_fits')
@mock.patch('conan.correct_tilt')
@mock.patch('conan.os.path.join', return_value='/mocked/path/export.csv')
def test_main(mock_join, mock_correct_tilt, mock_perform_fits, mock_set_surface_line, 
              mock_extract_drop_profile, mock_set_drop_region, mock_get_image, 
              mock_call_user_input):
    from conan import main, ExperimentalSetup, ExtractedData, DropData, Tolerances
    
    # Mock experimental setup
    user_inputs = mock.MagicMock()
    user_inputs.number_of_frames = 2
    user_inputs.import_files = ['image1.png', 'image2.png']
    user_inputs.ML_boole = False

    with mock.patch('conan.ExperimentalSetup', return_value=user_inputs), \
         mock.patch('conan.ExtractedData', return_value=mock.MagicMock()), \
         mock.patch('conan.ExperimentalDrop'), \
         mock.patch('conan.timeit.default_timer', side_effect=[0, 1, 2]):
        
        main()

    # Check if key functions are called
    assert mock_call_user_input.called
    assert mock_get_image.call_count == 2
    assert mock_set_drop_region.call_count == 2
    assert mock_extract_drop_profile.call_count == 2
    assert mock_set_surface_line.call_count == 2
    assert not mock_correct_tilt.called  # Should not be called when ML_boole is False

