import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
import numpy as np
import cv2
from modules.circular_fit import (
    circular_fit,
    circular_fit_img,
    extract_edges_CV,
    circle_fit_errors
)

# Generate circular test data
def generate_circle_points(center, radius, num_points=100):
    """Generate a set of circular points for testing"""
    angles = np.linspace(0, 2 * np.pi, num_points)
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    return np.column_stack((x, y))

@pytest.fixture
def sample_circle():
    """Generate a standard circular dataset as test input"""
    return generate_circle_points(center=(50, 50), radius=20, num_points=100)

@pytest.fixture
def sample_image():
    """Create a test image containing a simulated circular boundary"""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(img, (50, 50), 20, (255, 255, 255), thickness=1)
    return img

def test_circular_fit(sample_circle):
    """Test whether circular_fit correctly fits the circular data"""
    CA, center, R, intercepts, errors, timings = circular_fit(sample_circle)

    assert np.isclose(center[0], 50, atol=2), f"Expected center x≈50, got {center[0]}"
    assert np.isclose(center[1], 50, atol=2), f"Expected center y≈50, got {center[1]}"
    assert np.isclose(R, 20, atol=2), f"Expected radius ≈20, got {R}"

def test_circular_fit_img(sample_image):
    """Test whether circular_fit_img can correctly extract edges and fit a circle"""
    CA, center, R, intercepts, errors, timings = circular_fit_img(sample_image)

    assert np.isclose(center[0], 50, atol=2), f"Expected center x≈50, got {center[0]}"
    assert np.isclose(center[1], 50, atol=2), f"Expected center y≈50, got {center[1]}"
    assert np.isclose(R, 20, atol=2), f"Expected radius ≈20, got {R}"

def test_circle_fit_errors(sample_circle):
    """Test whether circle_fit_errors correctly calculates the fitting errors"""
    errors = circle_fit_errors(sample_circle, h=50, k=50, r=20)

    assert np.isclose(errors['MAE'], 0, atol=0.5)
    assert np.isclose(errors['MSE'], 0, atol=0.5)
    assert np.isclose(errors['RMSE'], 0, atol=0.5)
    assert np.isclose(errors['Maximum error'], 0, atol=1)

def test_extract_edges_CV(sample_image):
    """Test whether extract_edges_CV correctly extracts edge points"""
    edges = extract_edges_CV(sample_image)
    assert len(edges) > 20, "Edge detection failed, not enough points detected"

# def test_empty_input():
#     """Test whether an empty input is handled correctly"""
#     with pytest.raises(ValueError):
#         circular_fit(np.array([]))

def test_invalid_shapes():
    """Test cases where the input data format is incorrect"""
    invalid_data = np.array([1, 2, 3])
    with pytest.raises(IndexError):
        circular_fit(invalid_data)