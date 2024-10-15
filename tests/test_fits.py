import pytest
from unittest.mock import MagicMock
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.fits import perform_fits

@pytest.fixture
def experimental_drop():
    # Mock the experimental_drop object with more realistic data
    drop = MagicMock()
    drop.drop_contour = np.array([
        (0, 0), (1, 2), (2, 4), (3, 5), (4, 4), (5, 2), (6, 0), (7, -1), (8, -2), (9, -1)
    ])

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
    # Test ellipse fit functionality
    try:
        perform_fits(experimental_drop, ellipse=True)
        assert 'ellipse fit' in experimental_drop.contact_angles
    except IndexError:
        pytest.fail("Ellipse fit failed due to insufficient data points.")
    except TypeError:
        pytest.fail("Ellipse fit failed due to type error, possibly incorrect data format.")
    except ValueError:
        pytest.fail("Ellipse fit failed due to value error, possibly invalid numerical values.")
    else:
        if all([
            'left angle' in experimental_drop.contact_angles['ellipse fit'],
            'right angle' in experimental_drop.contact_angles['ellipse fit'],
            experimental_drop.contact_angles['ellipse fit']['left angle'] is not None,
            experimental_drop.contact_angles['ellipse fit']['right angle'] is not None
        ]):
            assert experimental_drop.contact_angles['ellipse fit']['left angle'] >= 0
            assert experimental_drop.contact_angles['ellipse fit']['right angle'] >= 0
        else:
            pytest.fail("Ellipse fit did not return valid angles.")

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
    sys.exit(pytest.main(["-q", __file__]))
