import pytest
import numpy as np
import sys
import os
from unittest import mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.preprocessing.ExtractData import ExtractedData

# 1. Test Object Initialization
def test_extracted_data_initialization():
    n_frames = 10
    n_params = 5
    data = ExtractedData(n_frames, n_params)
    
    # Check initialization of attributes
    assert data.initial_image_time is None
    assert len(data.time) == n_frames
    assert len(data.gamma_IFT_mN) == n_frames
    assert len(data.pixels_to_mm) == n_frames
    assert len(data.volume) == n_frames
    assert len(data.area) == n_frames
    assert len(data.worthington) == n_frames
    assert data.parameters.shape == (n_frames, n_params)
    assert data.contact_angles.shape == (n_frames, 2)

def test_zero_frames():
    # Test case with zero frames
    n_frames = 0
    n_params = 5
    data = ExtractedData(n_frames, n_params)
    
    # Ensure arrays are initialized with zero length
    assert data.time.size == 0
    assert data.parameters.shape == (0, n_params)

def test_zero_params():
    # Test case with zero parameters
    n_frames = 10
    n_params = 0
    data = ExtractedData(n_frames, n_params)

    # Ensure parameters array is initialized correctly
    assert data.parameters.shape == (n_frames, 0)

def test_negative_frames():
    # Test case with negative frames (should raise an exception or handle gracefully)
    with pytest.raises(ValueError):
        ExtractedData(-5, 5)

# 2. Test time_IFT_vol_area Method
def test_time_IFT_vol_area():
    n_frames = 10
    n_params = 5
    data = ExtractedData(n_frames, n_params)
    
    # Simulate some values for the first frame
    index = 0
    data.time[index] = 1.0
    data.gamma_IFT_mN[index] = 2.0
    data.volume[index] = 3.0
    data.area[index] = 4.0

    result = data.time_IFT_vol_area(index)
    
    # Expected result for frame 0
    expected = [1.0, 2.0, 3.0, 4.0]
    
    assert result == expected

def test_time_IFT_vol_area_index_out_of_bounds():
    # Test index out of bounds for time_IFT_vol_area
    n_frames = 5
    n_params = 5
    data = ExtractedData(n_frames, n_params)

    with pytest.raises(IndexError):
        data.time_IFT_vol_area(n_frames)  # Index out of bounds

# 3. Test export_data Method (Mocking file writing)
@mock.patch("builtins.open", new_callable=mock.mock_open)
def test_export_data(mock_open):
    n_frames = 10
    n_params = 5
    data = ExtractedData(n_frames, n_params)
    
    # Set mock values
    input_file = "input.csv"
    filename = "output.csv"
    i = 0
    
    # Simulate contact angles dictionary-like structure for the test
    data.contact_angles = {'ML model': {"left_angle": 45.0, "right_angle": 47.0}}
    
    # Call the method
    data.export_data(input_file, filename, i)
    
    # Verify file was opened with the correct filename
    mock_open.assert_called_with('./outputs/' + filename, 'a')
    
    # Check that the content was written
    mock_open().write.assert_any_call("Filename,Time (s),ML model left_angle,ML model right_angle\n")
    mock_open().write.assert_any_call('input.csv,')
    mock_open().write.assert_any_call('0.0,')
    mock_open().write.assert_any_call('45.0,')
    mock_open().write.assert_any_call('47.0,')
    mock_open().write.assert_any_call('\n')

@mock.patch("builtins.open", new_callable=mock.mock_open)
def test_export_data_index_out_of_bounds(mock_open):
    # Test index out of bounds for export_data
    n_frames = 5
    n_params = 5
    data = ExtractedData(n_frames, n_params)
    input_file = "input.csv"
    filename = "output.csv"
    
    with pytest.raises(IndexError):
        data.export_data(input_file, filename, n_frames)  # Index out of bounds