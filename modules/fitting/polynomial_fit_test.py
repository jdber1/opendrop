import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
import warnings

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from modules.fitting.polynomial_fit import *

warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestPolynomialFit(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        self.sample_data = np.array([[1, 1], [1.1, 1.1], [0, 5], [0.1, 5.1], [5, 0], [5.1, 0.1]])
        self.sample_profile = np.array([[0, 0], [1, 1], [2, 2], [3, 1], [4, 0]])

    def test_cluster_OPTICS(self):
        """Test OPTICS clustering algorithm"""
        # Test with xi parameter
        result1 = cluster_OPTICS(self.sample_data, xi=0.05)
        self.assertIsInstance(result1, dict)
        self.assertGreater(len(result1), 0)

        # Test with eps parameter
        result2 = cluster_OPTICS(self.sample_data, eps=0.5)
        self.assertIsInstance(result2, dict)
        self.assertGreater(len(result2), 0)

        # Test output format
        result3 = cluster_OPTICS(self.sample_data, out_style='xy', eps=0.5)
        self.assertIsInstance(result3, dict)
        self.assertTrue(any('x' in key for key in result3.keys()))

    def test_distance1(self):
        """Test function for calculating distance between two points"""
        self.assertAlmostEqual(distance1([0, 0], [3, 4]), 5.0)
        self.assertAlmostEqual(distance1([1, 1], [4, 5]), 5.0)
        self.assertEqual(distance1([0, 0], [0, 0]), 0.0)

    def test_optimized_path(self):
        """Test path optimization function"""
        path = optimized_path(self.sample_data)
        self.assertLessEqual(len(path), len(self.sample_data))
        for i in range(1, len(path)):
            self.assertLess(distance1(path[i-1], path[i]), 5)
            
    @patch('modules.fitting.polynomial_fit.plt.show')
    def test_prepare_hydrophobic(self, mock_show):
        """Test preprocessing of hydrophobic surface data"""
        profile, CPs = prepare_hydrophobic(self.sample_profile, display=True)
        self.assertIsInstance(profile, np.ndarray)
        self.assertIsInstance(CPs, dict)
        self.assertEqual(len(CPs), 2)

    # def test_find_contours(self):
    #     """Test contour detection function"""
    #     test_image = np.zeros((10, 10), dtype=np.uint8)
    #     test_image[2:8, 2:8] = 255
    #     contours = find_contours(test_image)
    #     self.assertIsInstance(contours, list)
    #     self.assertGreater(len(contours), 0)

    @patch('modules.fitting.polynomial_fit.cv2.cvtColor')
    @patch('modules.fitting.polynomial_fit.cv2.threshold')
    @patch('modules.fitting.polynomial_fit.cv2.findContours')
    def test_extract_edges_CV(self, mock_findContours, mock_threshold, mock_cvtColor):
        """Test CV edge extraction function"""
        mock_cvtColor.return_value = np.zeros((10, 10))
        mock_threshold.return_value = (None, np.zeros((10, 10)))
        mock_findContours.return_value = ([np.array([[[0, 0]], [[1, 1]]])], None)
        
        test_img = np.zeros((10, 10, 3))
        result = extract_edges_CV(test_img)
        self.assertIsInstance(result, np.ndarray)
        self.assertTrue(result.ndim in [1, 2])

    def test_polynomial_closest_point(self):
        """Test calculation of closest point on polynomial"""
        poly_points = np.array([[0, 0], [1, 1], [2, 2]])
        dist, point = polynomial_closest_point(0.5, 0.5, poly_points)
        self.assertIsInstance(dist, (int, float))
        self.assertEqual(len(point), 2)

    def test_polynomial_fit_errors(self):
        """Test polynomial fitting error calculations"""
        pts1 = np.array([[0, 0], [1, 1]])
        pts2 = np.array([[2, 2], [3, 3]])
        fit_left = np.poly1d([1, 0])  # y = x
        fit_right = np.poly1d([1, 0])  # y = x
        
        errors = polynomial_fit_errors(pts1, pts2, fit_left, fit_right)
        self.assertIsInstance(errors, dict)
        self.assertIn('MAE', errors)
        self.assertIn('MSE', errors)
        self.assertIn('RMSE', errors)

    @patch('modules.fitting.polynomial_fit.extract_edges_CV')
    @patch('modules.fitting.polynomial_fit.prepare_hydrophobic')
    def test_polynomial_fit_img(self, mock_prepare, mock_extract):
        """Test polynomial fitting for image"""
        mock_extract.return_value = self.sample_data
        mock_prepare.return_value = (self.sample_profile, {0: [0, 0], 1: [4, 0]})
        
        img = np.zeros((10, 10, 3))
        angles, intercepts, errors, timings = polynomial_fit_img(img)
        
        self.assertEqual(len(angles), 2)
        self.assertEqual(len(intercepts), 2)
        self.assertIsInstance(errors, dict)
        self.assertIsInstance(timings, dict)

    def test_polynomial_fit(self):
        """Test polynomial fitting function"""
        angles, CPs, tangent_lines, errors, timings = polynomial_fit(self.sample_profile)
        
        self.assertEqual(len(angles), 2)
        self.assertEqual(len(CPs), 2)
        self.assertEqual(len(tangent_lines), 2)
        self.assertIsInstance(errors, dict)
        self.assertIsInstance(timings, dict)

if __name__ == '__main__':
    unittest.main()