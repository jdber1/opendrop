import pytest
import numpy as np
import warnings
from unittest.mock import patch, MagicMock
import sys
import os
import cv2

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.fitting.BA_fit import *

# 定义 OpenCV 版本变量
CV2_VERSION = tuple(map(int, cv2.__version__.split(".")))

# 忽略警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ===== Fixtures =====
@pytest.fixture
def sample_data():
    return np.array([[1, 1], [1.1, 1.1], [0, 5], [0.1, 5.1], [5, 0], [5.1, 0.1]])

@pytest.fixture
def sample_profile():
    return np.array([[0, 0], [1, 1], [2, 2], [3, 1], [4, 0]])

# ===== Tests =====

def test_cluster_OPTICS(sample_data):
    result = cluster_OPTICS(sample_data, xi=0.05)
    assert isinstance(result, dict)
    assert len(result) > 0

def test_distance1():
    assert distance1([0, 0], [3, 4]) == pytest.approx(5.0)

def test_dist():
    params = [0, 0, 1]
    points = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
    assert dist(params, points) == pytest.approx(0.0)

def test_optimized_path(sample_data):
    path = optimized_path(sample_data)
    assert len(path) <= len(sample_data)
    for i in range(1, len(path)):
        assert distance1(path[i-1], path[i]) < 5

@patch('modules.fitting.BA_fit.plt.show')
def test_prepare_hydrophobic(mock_show, sample_profile):
    profile, CPs = prepare_hydrophobic(sample_profile, display=True)
    assert isinstance(profile, np.ndarray)
    assert isinstance(CPs, dict)

def test_bashforth_adams():
    result = bashforth_adams(0, [1, 1], 1, 1)
    assert isinstance(result, tuple)
    assert len(result) == 2

@patch('modules.fitting.BA_fit.solve_ivp')
def test_sim_bashforth_adams(mock_solve_ivp):
    mock_solve_ivp.return_value = MagicMock(t=np.array([0, 1]), y=np.array([[1, 1], [2, 2]]))
    angles, pred, Bo = sim_bashforth_adams(1, 1, 1)
    assert isinstance(angles, np.ndarray)
    assert isinstance(pred, np.ndarray)
    assert isinstance(Bo, float)

@patch('modules.fitting.BA_fit.opt.minimize')
def test_fit_bashforth_adams(mock_minimize, sample_profile):
    mock_minimize.return_value = MagicMock(x=[1, 1])
    result = fit_bashforth_adams(sample_profile)
    assert isinstance(result, MagicMock)

def test_calculate_angle():
    angle = calculate_angle(np.array([1, 0]), np.array([0, 1]))
    assert angle == pytest.approx(90.0)

@patch('modules.fitting.BA_fit.opt.minimize')
def test_fit_circle(mock_minimize, sample_profile):
    mock_minimize.return_value = {'x': [0, 0, 1], 'fun': 0.1}
    result = fit_circle(sample_profile)
    assert isinstance(result, dict)

def test_generate_circle_vectors():
    v1, v2 = generate_circle_vectors([1, 0])
    assert np.allclose(v1, [-1, 0])
    assert np.allclose(v2, [0, 1])

def test_find_intersection():
    baseline_coeffs = [0, 1]
    circ_params = [0, 0, 1]
    x_t, y_t = find_intersection(baseline_coeffs, circ_params)
    assert x_t == pytest.approx(1.0)
    assert y_t == pytest.approx(0.0)

# @patch('modules.fitting.BA_fit.cv2.findContours')
# def test_find_contours(mock_findContours):
#     mock_findContours.return_value = ([np.array([[[0, 0]], [[1, 1]]])], None)
#     image = np.ones((10, 10), dtype=np.uint8)
#     contours = find_contours(image)
#     assert isinstance(contours, list)
#     assert len(contours) == 1
#     assert np.array_equal(contours[0], np.array([[0, 0], [1, 1]]))

@patch('modules.fitting.BA_fit.plt.show')
@patch('modules.fitting.BA_fit.fit_circle', return_value={'x': [0, 0, 1], 'fun': 0.1})
@patch('modules.fitting.BA_fit.find_intersection', return_value=(0.5, 0.5))
@patch('modules.fitting.BA_fit.generate_circle_vectors', return_value=([1, 0], [0, 1]))
@patch('modules.fitting.BA_fit.calculate_angle', return_value=90)
@patch('modules.fitting.BA_fit.fit_bashforth_adams', return_value=MagicMock(x=[1, 1]))
@patch('modules.fitting.BA_fit.sim_bashforth_adams', return_value=(np.array([0, 90]), np.array([[0, 0], [1, 1]]), 1.0))
def test_YL_fit(mock_sim, mock_fit, mock_calc, mock_gen, mock_find, mock_circle, mock_show, sample_profile):
    result = YL_fit(sample_profile, display=True)
    assert isinstance(result, tuple)
    assert len(result) == 9

# Optional: run directly
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
