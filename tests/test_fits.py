import pytest
from unittest.mock import MagicMock
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.fits import perform_fits

@pytest.fixture
def experimental_drop():
    drop = MagicMock()
    # Create a half-ellipse shape representing a drop (upper half) plus a flat bottom line
    theta = np.linspace(0, np.pi, 50)  # Only the upper half of the ellipse
    a, b = 50, 30
    x = a * np.cos(theta)
    y = b * np.sin(theta)
    
    # Add a flat bottom line to simulate the drop's contact with a surface
    x_base = np.linspace(-a, a, 20)
    y_base = np.zeros_like(x_base)
    
    # Combine the upper ellipse and the bottom line
    x_full = np.concatenate([x_base, x[::-1]])
    y_full = np.concatenate([y_base, y[::-1]])
    
    drop.drop_contour = np.column_stack((x_full, y_full))
    drop.contact_angles = {}
    return drop




def test_perform_fits_tangent(experimental_drop):
    # Test tangent fit functionality
    perform_fits(experimental_drop, tangent=True)
    assert 'tangent fit' in experimental_drop.contact_angles
    assert 'left angle' in experimental_drop.contact_angles['tangent fit']
    assert 'right angle' in experimental_drop.contact_angles['tangent fit']
    assert experimental_drop.contact_angles['tangent fit']['left angle'] >= 0
    assert experimental_drop.contact_angles['tangent fit']['right angle'] >= 0

def test_perform_fits_polynomial(experimental_drop):
    # Test polynomial fit functionality as implemented in perform_fits
    perform_fits(experimental_drop, polynomial=True)
    assert 'polynomial fit' in experimental_drop.contact_angles
    assert 'left angle' in experimental_drop.contact_angles['polynomial fit']
    assert 'right angle' in experimental_drop.contact_angles['polynomial fit']
    assert experimental_drop.contact_angles['polynomial fit']['left angle'] >= 0
    assert experimental_drop.contact_angles['polynomial fit']['right angle'] >= 0

def test_perform_fits_circle(experimental_drop):
    # Test circle fit functionality
    perform_fits(experimental_drop, circle=True)
    assert 'circle fit' in experimental_drop.contact_angles
    assert 'left angle' in experimental_drop.contact_angles['circle fit']
    assert 'right angle' in experimental_drop.contact_angles['circle fit']
    assert 'circle center' in experimental_drop.contact_angles['circle fit']
    assert 'circle radius' in experimental_drop.contact_angles['circle fit']
    assert experimental_drop.contact_angles['circle fit']['left angle'] >= 0
    assert experimental_drop.contact_angles['circle fit']['right angle'] >= 0
    assert experimental_drop.contact_angles['circle fit']['circle radius'] > 0

def test_perform_fits_ellipse(experimental_drop):
    try:
        perform_fits(experimental_drop, ellipse=True)
    except Exception as e:
        pytest.fail(f"Ellipse fit failed: {e}")
    
    assert 'ellipse fit' in experimental_drop.contact_angles
    data = experimental_drop.contact_angles['ellipse fit']
    
    required_keys = ['left angle', 'right angle', 'ellipse center', 'ellipse a and b', 'ellipse rotation']
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    
    # Check if the absolute value of the angles is positive (since negative angles are also valid)
    assert abs(data['left angle']) > 0, "Left angle absolute value should be positive"
    assert abs(data['right angle']) > 0, "Right angle absolute value should be positive"

def test_perform_fits_YL(experimental_drop):
    # Test YL fit functionality
    perform_fits(experimental_drop, YL=True)
    assert 'YL fit' in experimental_drop.contact_angles
    assert 'left angle' in experimental_drop.contact_angles['YL fit']
    assert 'right angle' in experimental_drop.contact_angles['YL fit']
    assert experimental_drop.contact_angles['YL fit']['left angle'] >= 0
    assert experimental_drop.contact_angles['YL fit']['right angle'] >= 0

# Run the tests
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
