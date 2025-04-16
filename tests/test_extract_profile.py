import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from modules.contact_angle.extract_profile import (
    extract_drop_profile,
    detect_edges,
    prepare_hydrophobic,
    cluster_OPTICS
)

# Fixtures ----------------------------------------------------------------

@pytest.fixture
def mock_raw_experiment():
    class RawExperiment:
        cropped_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        ret = None
        contour = None
    return RawExperiment()

@pytest.fixture
def mock_user_inputs():
    class UserInputs:
        threshold_method = "User-selected"
        drop_region = [(10, 10), (90, 90)]
        threshold_val = 127
    return UserInputs()

@pytest.fixture
def mock_contour_data():
    return np.array([[50, 150], [55, 145], [60, 140], [65, 135]], dtype=np.float32)

# Core Function Tests -----------------------------------------------------

@patch("cv2.threshold")
@patch("cv2.GaussianBlur")
def test_manual_threshold_processing(mock_blur, mock_threshold, mock_raw_experiment, mock_user_inputs):
    """Test Case 1: Verify manual threshold processing"""
    # Mock OpenCV returns
    mock_threshold.return_value = (127, np.zeros_like(mock_raw_experiment.cropped_image))
    
    extract_drop_profile(mock_raw_experiment, mock_user_inputs)
    
    # Verify threshold call with manual value
    mock_threshold.assert_called_once()
    assert mock_raw_experiment.ret == 127
    assert mock_raw_experiment.contour is not None

@patch("cv2.threshold")
def test_otsu_auto_threshold(mock_threshold, mock_raw_experiment, mock_user_inputs):
    """Test Case 2: Validate OTSU auto threshold calculation"""
    mock_user_inputs.threshold_method = "Automated"
    mock_threshold.return_value = (127, np.zeros_like(mock_raw_experiment.cropped_image))
    
    extract_drop_profile(mock_raw_experiment, mock_user_inputs)
    
    # Verify automatic threshold range
    assert 0 <= mock_raw_experiment.ret <= 255
    assert mock_threshold.call_args[1]['thresh'] == 0  # OTSU flag check

@patch("cv2.findContours")
def test_contour_trimming(mock_findContours, mock_raw_experiment):
    """Test Case 3: Verify edge boundary filtering"""
    # Mock contour data with boundary points
    test_contour = np.array([[[0,0]], [[99,99]], [[50,50]]], dtype=np.int32)
    mock_findContours.return_value = ([test_contour], None)
    
    contour, _ = detect_edges(np.zeros((100,100)), None, None, 1, 127)
    
    # Verify boundary points removed
    assert not any((contour[:,0] == 0) | (contour[:,0] == 99) | 
                   (contour[:,1] == 0) | (contour[:,1] == 99))

# Clustering & Contact Point Tests ----------------------------------------

def test_contact_point_detection(mock_contour_data):
    """Test Case 4: Verify hydrophobic contact point identification"""
    profile, cps = prepare_hydrophobic(mock_contour_data)
    
    # Validate CP structure and coordinates
    assert len(cps) == 2
    assert abs(cps[0][1] - cps[1][1]) < 1e-6  # Matching Y coordinates

# Error Handling Tests ----------------------------------------------------

def test_invalid_threshold_handling(mock_raw_experiment):
    """Test Case 5: Validate out-of-range threshold handling"""
    with pytest.raises(ValueError):
        detect_edges(np.zeros((100,100)), None, None, 1, 300)

def test_empty_input_handling():
    """Test Case 6: Verify empty array processing"""
    with pytest.raises(ValueError):
        prepare_hydrophobic(np.empty((0,2)))

# Edge Case Tests ---------------------------------------------------------

def test_low_contrast_image_processing():
    """Edge Case: Process low contrast image (Δgrayscale <10)"""
    low_contrast_img = np.full((100,100), 127, dtype=np.uint8)
    contour, _ = detect_edges(low_contrast_img, None, None, 1, 127)
    assert len(contour) > 0  # Should still return valid contour

@patch("cv2.findContours")
def test_high_noise_handling(mock_findContours):
    """Edge Case: Handle high-noise images (simulated)"""
    # Mock fragmented contours
    mock_findContours.return_value = ([np.random.randint(0,100,(50,1,2)) for _ in range(10)], None)
    contour, _ = detect_edges(np.zeros((100,100)), None, None, 1, 127)
    assert len(contour) > 0  # Should return consolidated contour

# Main Execution ----------------------------------------------------------
if __name__ == "__main__":
    pytest.main()
