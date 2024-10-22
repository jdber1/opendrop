import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
import warnings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.BA_fit import *

# 忽略 np.float 的废弃警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestBAFit(unittest.TestCase):

    def setUp(self):
        self.sample_data = np.array([[1, 1], [1.1, 1.1], [0, 5], [0.1, 5.1], [5, 0], [5.1, 0.1]])
        self.sample_profile = np.array([[0, 0], [1, 1], [2, 2], [3, 1], [4, 0]])

    def test_cluster_OPTICS(self):
        result = cluster_OPTICS(self.sample_data, xi=0.05)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_distance1(self):
        self.assertAlmostEqual(distance1([0, 0], [3, 4]), 5.0)

    def test_dist(self):
        params = [0, 0, 1]  # center (0,0) and radius 1
        points = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        self.assertAlmostEqual(dist(params, points), 0.0)

    def test_optimized_path(self):
        path = optimized_path(self.sample_data)
        self.assertLessEqual(len(path), len(self.sample_data))
        for i in range(1, len(path)):
            self.assertLess(distance1(path[i-1], path[i]), 5)

    @patch('modules.BA_fit.plt.show')
    def test_prepare_hydrophobic(self, mock_show):
        profile, CPs = prepare_hydrophobic(self.sample_profile, display=True)
        self.assertIsInstance(profile, np.ndarray)
        self.assertIsInstance(CPs, dict)

    def test_bashforth_adams(self):
        result = bashforth_adams(0, [1, 1], 1, 1)
        self.assertEqual(len(result), 2)

    @patch('modules.BA_fit.solve_ivp')
    def test_sim_bashforth_adams(self, mock_solve_ivp):
        mock_solve_ivp.return_value = MagicMock(t=np.array([0, 1]), y=np.array([[1, 1], [2, 2]]))
        angles, pred, Bo = sim_bashforth_adams(1, 1, 1)
        self.assertIsInstance(angles, np.ndarray)
        self.assertIsInstance(pred, np.ndarray)
        self.assertIsInstance(Bo, float)

    @patch('modules.BA_fit.opt.minimize')
    def test_fit_bashforth_adams(self, mock_minimize):
        mock_minimize.return_value = MagicMock(x=[1, 1])
        result = fit_bashforth_adams(self.sample_profile)
        self.assertIsInstance(result, MagicMock)

    def test_calculate_angle(self):
        angle = calculate_angle(np.array([1, 0]), np.array([0, 1]))
        self.assertAlmostEqual(angle, 90.0)

    @patch('modules.BA_fit.opt.minimize')
    def test_fit_circle(self, mock_minimize):
        mock_minimize.return_value = {'x': [0, 0, 1], 'fun': 0.1}
        result = fit_circle(self.sample_profile)
        self.assertIsInstance(result, dict)

    def test_generate_circle_vectors(self):
        v1, v2 = generate_circle_vectors([1, 0])
        self.assertTrue(np.allclose(v1, [-1, 0]))
        self.assertTrue(np.allclose(v2, [0, 1]))

    def test_find_intersection(self):
        baseline_coeffs = [0, 1]  # y = x
        circ_params = [0, 0, 1]  # center (0,0), radius 1
        x_t, y_t = find_intersection(baseline_coeffs, circ_params)
        self.assertAlmostEqual(x_t, 1.0, places=7)
        self.assertAlmostEqual(y_t, 0.0, places=7)

    @patch('modules.BA_fit.cv2.findContours')
    def test_find_contours(self, mock_findContours):
        mock_findContours.return_value = ([np.array([[[0, 0]], [[1, 1]]])], None)
        image = np.ones((10, 10), dtype=np.uint8)
        contours = find_contours(image)
        self.assertIsInstance(contours, list)
        self.assertEqual(len(contours), 1)
        self.assertTrue(np.array_equal(contours[0], np.array([[0, 0], [1, 1]])))

    @patch('modules.BA_fit.cv2')
    def test_extract_edges_CV(self, mock_cv2):
        mock_cv2.cvtColor.return_value = np.ones((10, 10), dtype=np.uint8)
        mock_cv2.threshold.return_value = (None, np.ones((10, 10), dtype=np.uint8))
        mock_cv2.findContours.return_value = ([np.array([[[0, 0]], [[1, 1]]])], None)
        mock_cv2.arcLength.return_value = 1.0
        result = extract_edges_CV(np.ones((10, 10, 3)))
        self.assertIsInstance(result, np.ndarray)
        self.assertTrue(result.ndim in [1, 2])

    @patch('modules.BA_fit.plt.show')
    @patch('modules.BA_fit.extract_edges_CV', return_value=np.array([[0, 0], [1, 1]]))
    @patch('modules.BA_fit.prepare_hydrophobic', return_value=(np.array([[0, 0], [1, 1]]), {0: [0, 0], 1: [1, 1]}))
    @patch('modules.BA_fit.fit_circle', return_value={'x': [0, 0, 1], 'fun': 0.1})
    @patch('modules.BA_fit.find_intersection', return_value=(0.5, 0.5))
    @patch('modules.BA_fit.generate_circle_vectors', return_value=([1, 0], [0, 1]))
    @patch('modules.BA_fit.calculate_angle', return_value=90)
    @patch('modules.BA_fit.fit_bashforth_adams', return_value=MagicMock(x=[1, 1]))
    @patch('modules.BA_fit.sim_bashforth_adams', return_value=(np.array([0, 90]), np.array([[0, 0], [1, 1]]), 1.0))
    @patch('modules.BA_fit.YL_fit_errors', return_value={'MAE': 0, 'MSE': 0, 'RMSE': 0, 'Maximum error': 0})
    def test_analyze_frame(self, mock_yl_errors, mock_sim, mock_fit, mock_calc, mock_gen, mock_find, mock_circle, mock_prepare, mock_extract, mock_show):
        result = analyze_frame(np.ones((10, 10, 3)), display=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 9)

    @patch('modules.BA_fit.plt.show')
    @patch('modules.BA_fit.fit_circle', return_value={'x': [0, 0, 1], 'fun': 0.1})
    @patch('modules.BA_fit.find_intersection', return_value=(0.5, 0.5))
    @patch('modules.BA_fit.generate_circle_vectors', return_value=([1, 0], [0, 1]))
    @patch('modules.BA_fit.calculate_angle', return_value=90)
    @patch('modules.BA_fit.fit_bashforth_adams', return_value=MagicMock(x=[1, 1]))
    @patch('modules.BA_fit.sim_bashforth_adams', return_value=(np.array([0, 90]), np.array([[0, 0], [1, 1]]), 1.0))
    def test_YL_fit(self, mock_sim, mock_fit, mock_calc, mock_gen, mock_find, mock_circle, mock_show):
        result = YL_fit(self.sample_profile, display=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 9)

if __name__ == '__main__':
    unittest.main()
