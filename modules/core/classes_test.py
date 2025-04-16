import pytest
import numpy as np
from math import pi

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.core.classes import Tolerances, ExperimentalSetup, ExperimentalDrop, DropData

@pytest.fixture
def test_tolerances():
    return Tolerances(
        delta_tol=1e-6,
        gradient_tol=1e-6,
        maximum_fitting_steps=100,
        objective_tol=1e-6,
        arclength_tol=1e-6,
        maximum_arclength_steps=100,
        needle_tol=1e-6,
        needle_steps=100
    )

@pytest.fixture
def test_experimental_setup():
    setup = ExperimentalSetup()
    setup.needle_diameter_mm = 1.0
    setup.user_input_fields['drop_density'] = 1000.0
    setup.user_input_fields['continuous_density'] = 0.0
    setup.user_input_fields['pixel_mm'] = 100.0
    return setup

@pytest.fixture
def test_experimental_drop():
    drop = ExperimentalDrop()
    drop.drop_contour = np.array([
        [0, 0], [1, 1], [2, 2], [3, 3], [4, 2], [5, 1], [6, 0]
    ])
    drop.contact_points = [[0, 0], [6, 0]]
    drop.pixels_to_mm = 100.0
    return drop

@pytest.fixture
def test_drop_data():
    data = DropData()
    # Initialize test parameters
    data._params = [0.0, 0.0, 1.0, 0.5, 0.0]
    data._max_s = 5.0
    data._s_points = 50
    # Manually call to generate theoretical data
    data.generate_profile_data()
    return data

def test_tolerances_initialization(test_tolerances):
    """Test that Tolerances is initialized with correct values"""
    tol = test_tolerances
    assert tol.DELTA_TOL == 1e-6
    assert tol.GRADIENT_TOL == 1e-6
    assert tol.MAXIMUM_FITTING_STEPS == 100
    assert tol.OBJECTIVE_TOL == 1e-6
    assert tol.ARCLENGTH_TOL == 1e-6
    assert tol.MAXIMUM_ARCLENGTH_STEPS == 100
    assert tol.NEEDLE_TOL == 1e-6
    assert tol.NEEDLE_STEPS == 100

def test_experimental_setup_initialization(test_experimental_setup):
    """Test that ExperimentalSetup is initialized with correct values"""
    setup = test_experimental_setup
    assert setup.needle_diameter_mm == 1.0
    assert setup.user_input_fields['drop_density'] == 1000.0
    assert setup.user_input_fields['continuous_density'] == 0.0
    assert setup.user_input_fields['pixel_mm'] == 100.0
    assert setup.drop_region is None  # Default value
    assert setup.needle_region is None  # Default value

def test_experimental_drop_initialization(test_experimental_drop):
    """Test that ExperimentalDrop is initialized with correct values"""
    drop = test_experimental_drop
    assert drop.pixels_to_mm == 100.0
    assert drop.image is None  # Default value
    assert drop.contact_angles == {}  # Default empty dict
    assert np.array_equal(drop.drop_contour, np.array([
        [0, 0], [1, 1], [2, 2], [3, 3], [4, 2], [5, 1], [6, 0]
    ]))
    assert drop.contact_points == [[0, 0], [6, 0]]

def test_drop_data_initialization(test_drop_data):
    """Test that DropData is initialized with correct values"""
    data = test_drop_data
    assert data.params == [0.0, 0.0, 1.0, 0.5, 0.0]
    assert data.max_s == 5.0
    assert data.s_points == 50
    assert data.parameter_dimensions == 5
    assert data.previous_guess is None
    assert data.previous_params is None

def test_drop_data_bond(test_drop_data):
    """Test that bond() returns the correct Bond number"""
    data = test_drop_data
    assert data.bond() == 0.5

def test_drop_data_apex_radius(test_drop_data):
    """Test that apex_radius() returns the correct value"""
    data = test_drop_data
    assert data.apex_radius() == 1.0

def test_drop_data_generate_profile(test_drop_data):
    """Test that generate_profile_data() creates theoretical data"""
    data = test_drop_data
    # Verify theoretical data has been generated
    assert data.theoretical_data is not None
    # Check data shape
    if data.theoretical_data is not None:
        assert data.theoretical_data.shape[0] == data.s_points + 1  # s_points + 1 rows
        assert data.theoretical_data.shape[1] == 6  # 6 columns (x, y, phi, x_Bond, y_Bond, phi_Bond)

def test_drop_data_params_setter():
    """Test that setting params regenerates profile"""
    # Create a new DropData instance to avoid issues with fixture
    data = DropData()
    data._max_s = 5.0
    data._s_points = 50
    data._params = [0.0, 0.0, 1.0, 0.5, 0.0]
    data.generate_profile_data()
    
    # Ensure theoretical data has been generated
    assert data.theoretical_data is not None
    original_shape = data.theoretical_data.shape
    
    # Change parameters
    new_params = [0.0, 0.0, 2.0, 0.3, 0.0]
    data.params = new_params
    
    # Check parameters were updated
    assert data.params == new_params
    
    # Check theoretical data was regenerated
    assert data.theoretical_data is not None
    assert data.theoretical_data.shape == original_shape

def test_drop_data_max_s_setter():
    """Test that setting max_s regenerates profile"""
    # Create a new DropData instance
    data = DropData()
    data._params = [0.0, 0.0, 1.0, 0.5, 0.0]
    data._s_points = 50
    data._max_s = 5.0
    data.generate_profile_data()
    
    # Ensure theoretical data has been generated
    assert data.theoretical_data is not None
    original_points = data.theoretical_data.shape[0]
    
    # Change max_s
    data.max_s = 10.0
    
    # Check max_s was updated
    assert data.max_s == 10.0
    
    # Check theoretical data was regenerated, but point count should remain the same
    assert data.theoretical_data is not None
    assert data.theoretical_data.shape[0] == original_points

def test_drop_data_s_points_setter():
    """Test that setting s_points regenerates profile"""
    # Create a new DropData instance
    data = DropData()
    data._params = [0.0, 0.0, 1.0, 0.5, 0.0]
    data._max_s = 5.0
    data._s_points = 50
    data.generate_profile_data()
    
    # Ensure theoretical data has been generated
    assert data.theoretical_data is not None
    original_points = data.theoretical_data.shape[0]
    
    # Change s_points
    data.s_points = 100
    
    # Check s_points was updated
    assert data.s_points == 100
    
    # Check theoretical data was regenerated with more points
    assert data.theoretical_data is not None
    assert data.theoretical_data.shape[0] == 101  # s_points + 1

def test_drop_data_invalid_params(test_drop_data):
    """Test that setting invalid params raises ValueError"""
    data = test_drop_data
    
    # Test with incorrect dimension
    with pytest.raises(ValueError):
        data.params = [0.0, 0.0, 1.0]  # Should be 5 values

def test_drop_data_invalid_max_s(test_drop_data):
    """Test that setting invalid max_s raises ValueError"""
    data = test_drop_data
    
    # Test with negative value
    with pytest.raises(ValueError):
        data.max_s = -1.0

def test_drop_data_invalid_s_points(test_drop_data):
    """Test that setting invalid s_points raises ValueError"""
    data = test_drop_data
    
    # Test with non-positive value
    with pytest.raises(ValueError):
        data.s_points = 0
    
    # Test with non-integer value
    with pytest.raises(ValueError):
        data.s_points = 50.5

if __name__ == "__main__":
    # Run pytest when script is executed directly
    pytest.main(["-v", __file__])