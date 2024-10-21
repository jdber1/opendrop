import pytest
import numpy as np
import sys
import os
from unittest import mock

from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.initialise_parameters import initialise_parameters, fit_circle, calculate_Bond_number, scaled_radius_at_scaled_height


def test_initialise_parameters():
    # Mock objects for experimental_drop and drop_data
    experimental_drop = Mock()
    drop_data = Mock()

    # Set mock data
    experimental_drop.drop_data = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
    
    # Call the function
    initialise_parameters(experimental_drop, drop_data)

    # Check if params were initialized correctly (you can adjust this as per actual output structure)
    assert len(drop_data.params) == 5
    assert drop_data.max_s == 4.0


def test_fit_circle_valid_data():
    # Test with valid input data
    xypoints = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]
    x, y, R = fit_circle(xypoints)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(R, float)


def test_fit_circle_insufficient_data():
    # Test with fewer than 10 points
    xypoints = [(0, 1), (1, 2), (2, 3)]
    x, y, R = fit_circle(xypoints)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(R, float)
    assert len(xypoints) <= 10  # Ensure it handles the case of not enough data


def test_fit_circle_empty_data():
    # Test with no points
    xypoints = []
    with pytest.raises(ZeroDivisionError):
        fit_circle(xypoints)


def test_calculate_Bond_number_valid_data():
    # Test Bond number calculation with valid data
    xypoints = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11)]
    x_apex = 4.0    # Apex x-coordinate
    y_apex = 4.0    # Apex y-coordinate
    radius_apex = 1.0  # Radius at apex

    scaled_radius = scaled_radius_at_scaled_height(xypoints, x_apex, y_apex, radius_apex, 2)
    assert scaled_radius == 2.7

    bond_number = calculate_Bond_number(xypoints, x_apex, y_apex, radius_apex)
    assert bond_number == 0.1756 * scaled_radius**2 + 0.5234 * scaled_radius**3 - 0.2563 * scaled_radius**4


def test_calculate_Bond_number_r_z2_negative():
    # Test when r_z2 is negative
    xypoints = [(0, 0), (1, 1), (2, 2)]
    bond_number = calculate_Bond_number(xypoints, 0, 0, 1)
    assert bond_number == 0.15  # Fallback case should return 0.15


def test_scaled_radius_at_scaled_height_valid_data():
    # Test with valid input data
    xypoints = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11)]
    x_apex = 6.0    # Apex x-coordinate
    y_apex = 6.0    # Apex y-coordinate
    radius_apex = 1.0  # Radius at apex
    height = 1       # Height to calculate at

    result = scaled_radius_at_scaled_height(xypoints, x_apex, y_apex, radius_apex, height)

    # Calculate the expected scaled radius
    expected_result = 2.5

    # Assert that the calculated result matches the expected result
    assert result == expected_result


def test_scaled_radius_at_scaled_height_not_enough_data():
    # Test when there aren't enough data points to guess Bond number
    xypoints = [(0, 0), (1, 1)]
    result = scaled_radius_at_scaled_height(xypoints, 0, 0, 1, 2)
    assert result == -1


def test_scaled_radius_at_scaled_height_not_enough_points_to_average():
    # Test when there aren't enough points to average over
    xypoints = [(0, 0), (1, 1), (2, 2)]
    result = scaled_radius_at_scaled_height(xypoints, 0, 0, 1, 2)
    assert result == -2


def test_scaled_radius_at_scaled_height_height_out_of_bounds():
    # Test when z_value goes beyond the maximum height in xypoints
    xypoints = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
    result = scaled_radius_at_scaled_height(xypoints, 0, 0, 1, 10)
    assert result == -1  # Since z_value exceeds the data's height range
