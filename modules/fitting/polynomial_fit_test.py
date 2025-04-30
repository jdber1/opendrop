import numpy as np


import pytest
from unittest.mock import patch
import sys
import os
import warnings

if not hasattr(np, 'float'):
    np.float = float

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from modules.fitting.polynomial_fit import *

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture
def sample_data():
    return np.array([[1, 1], [1.1, 1.1], [0, 5], [0.1, 5.1], [5, 0], [5.1, 0.1]])


@pytest.fixture
def sample_profile():
    return np.array([[0, 0], [1, 1], [2, 2], [3, 1], [4, 0]])


def test_cluster_OPTICS(sample_data):
    result1 = cluster_OPTICS(sample_data, xi=0.05)
    assert isinstance(result1, dict)
    assert len(result1) > 0

    result2 = cluster_OPTICS(sample_data, eps=0.5)
    assert isinstance(result2, dict)
    assert len(result2) > 0

    result3 = cluster_OPTICS(sample_data, out_style='xy', eps=0.5)
    assert isinstance(result3, dict)
    assert any('x' in key for key in result3.keys())


def test_distance1():
    assert distance1([0, 0], [3, 4]) == pytest.approx(5.0)
    assert distance1([1, 1], [4, 5]) == pytest.approx(5.0)
    assert distance1([0, 0], [0, 0]) == 0.0


def test_optimized_path(sample_data):
    path = optimized_path(sample_data)
    assert len(path) <= len(sample_data)
    for i in range(1, len(path)):
        assert distance1(path[i - 1], path[i]) < 5


@patch('modules.fitting.polynomial_fit.plt.show')
def test_prepare_hydrophobic(mock_show, sample_profile):
    profile, CPs = prepare_hydrophobic(sample_profile, display=True)
    assert isinstance(profile, np.ndarray)
    assert isinstance(CPs, dict)
    assert len(CPs) == 2


# def test_find_contours():
#     test_image = np.zeros((10, 10), dtype=np.uint8)
#     test_image[2:8, 2:8] = 255
#     contours = find_contours(test_image)
#     assert isinstance(contours, list)
#     assert len(contours) > 0

@patch('modules.fitting.polynomial_fit.cv2.cvtColor')
@patch('modules.fitting.polynomial_fit.cv2.threshold')
@patch('modules.fitting.polynomial_fit.cv2.findContours')
def test_extract_edges_CV(mock_findContours, mock_threshold, mock_cvtColor):
    mock_cvtColor.return_value = np.zeros((10, 10))
    mock_threshold.return_value = (None, np.zeros((10, 10)))
    mock_findContours.return_value = ([np.array([[[0, 0]], [[1, 1]]])], None)

    test_img = np.zeros((10, 10, 3))
    result = extract_edges_CV(test_img)
    assert isinstance(result, np.ndarray)
    assert result.ndim in [1, 2]


def test_polynomial_closest_point():
    poly_points = np.array([[0, 0], [1, 1], [2, 2]])
    dist, point = polynomial_closest_point(0.5, 0.5, poly_points)
    assert isinstance(dist, (int, float))
    assert len(point) == 2


def test_polynomial_fit_errors():
    pts1 = np.array([[0, 0], [1, 1]])
    pts2 = np.array([[2, 2], [3, 3]])
    fit_left = np.poly1d([1, 0])  # y = x
    fit_right = np.poly1d([1, 0])  # y = x

    errors = polynomial_fit_errors(pts1, pts2, fit_left, fit_right)
    assert isinstance(errors, dict)
    assert 'MAE' in errors
    assert 'MSE' in errors
    assert 'RMSE' in errors


@patch('modules.fitting.polynomial_fit.extract_edges_CV')
@patch('modules.fitting.polynomial_fit.prepare_hydrophobic')
def test_polynomial_fit_img(mock_prepare, mock_extract, sample_data, sample_profile):
    mock_extract.return_value = sample_data
    mock_prepare.return_value = (sample_profile, {0: [0, 0], 1: [4, 0]})

    img = np.zeros((10, 10, 3))
    angles, intercepts, errors, timings = polynomial_fit_img(img)

    assert len(angles) == 2
    assert len(intercepts) == 2
    assert isinstance(errors, dict)
    assert isinstance(timings, dict)


def test_polynomial_fit(sample_profile):
    angles, CPs, tangent_lines, errors, timings = polynomial_fit(sample_profile)

    assert len(angles) == 2
    assert len(CPs) == 2
    assert len(tangent_lines) == 2
    assert isinstance(errors, dict)
    assert isinstance(timings, dict)
