import pytest
import numpy as np
from math import pi

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.de_YoungLaplace import ylderiv, dataderiv

@pytest.fixture
def yl_parameters():
    return {
        'bond_number': 0.5,
        'bond_number_negative': -0.5,
        'x_vec_yl': [1.0, 1.0, pi/4, 0.5, 0.5, 0.1],  # x, y, phi, x_Bond, y_Bond, phi_Bond
        'x_vec_data': [1.0, 1.0, pi/4, 0.0, 2*pi],    # x, y, phi, vol, sur
        't': 0.0,
        'tolerance': 1e-10
    }

def test_ylderiv(yl_parameters):
    # Get test parameters from fixture
    x_vec = yl_parameters['x_vec_yl']
    t = yl_parameters['t']
    bond_number = yl_parameters['bond_number']
    tolerance = yl_parameters['tolerance']
    
    # Calculate the derivatives
    result = ylderiv(x_vec, t, bond_number)
    
    # Expected values (calculated manually or with a reference implementation)
    expected = [
        np.cos(pi/4),  # x_s
        np.sin(pi/4),  # y_s
        2 + bond_number * x_vec[1] - np.sin(pi/4)/x_vec[0],  # phi_s
        -np.sin(pi/4) * x_vec[5],  # x_Bond_s
        np.cos(pi/4) * x_vec[5],  # y_Bond_s
        np.sin(pi/4) * x_vec[3] / (x_vec[0]**2) - np.cos(pi/4) * x_vec[5] / x_vec[0] - x_vec[1] - bond_number * x_vec[4]  # phi_Bond_s
    ]
    
    # Check that each component matches the expected value within tolerance
    for i in range(len(result)):
        assert abs(result[i] - expected[i]) < tolerance, f"Component {i} mismatch: {result[i]} != {expected[i]}"

def test_dataderiv(yl_parameters):
    # Get test parameters from fixture
    x_vec = yl_parameters['x_vec_data']
    t = yl_parameters['t']
    bond_number = yl_parameters['bond_number']
    tolerance = yl_parameters['tolerance']
    
    # Calculate the derivatives
    result = dataderiv(x_vec, t, bond_number)
    
    # Expected values
    expected = [
        np.cos(pi/4),  # x_s
        np.sin(pi/4),  # y_s
        2 - bond_number * x_vec[1] - np.sin(pi/4)/x_vec[0],  # phi_s
        pi * x_vec[0]**2 * np.sin(pi/4),  # vol_s
        2 * pi * x_vec[0]  # sur_s
    ]
    
    # Check that each component matches the expected value within tolerance
    for i in range(len(result)):
        assert abs(result[i] - expected[i]) < tolerance, f"Component {i} mismatch: {result[i]} != {expected[i]}"

def test_ylderiv_sign_change(yl_parameters):
    """Test for the sign change mentioned in the comment (DS 16/09 2- made 2+ for contact angle)"""
    # Get test parameters from fixture
    x_vec = yl_parameters['x_vec_yl']
    t = yl_parameters['t']
    bond_positive = yl_parameters['bond_number']
    bond_negative = yl_parameters['bond_number_negative']
    tolerance = yl_parameters['tolerance']
    
    # Calculate with positive bond number
    result_positive = ylderiv(x_vec, t, bond_positive)
    
    # Calculate with negative bond number
    result_negative = ylderiv(x_vec, t, bond_negative)
    
    # The phi_s component (index 2) should reflect the sign change
    assert result_positive[2] != result_negative[2], "Sign change in bond number should affect phi_s"
    
    # Specifically, for the same magnitude but opposite sign bond numbers,
    # the difference in phi_s should be proportional to the bond number difference times y
    bond_diff = bond_positive - bond_negative
    expected_phi_s_diff = bond_diff * x_vec[1]  # bond_diff * y
    actual_phi_s_diff = result_positive[2] - result_negative[2]
    
    assert abs(actual_phi_s_diff - expected_phi_s_diff) < tolerance, "Sign change effect incorrect"

    # Run the tests
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
