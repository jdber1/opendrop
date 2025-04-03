import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import unittest
import numpy as np
from itertools import cycle
from modules.fits import perform_fits
from modules.preprocessing import prepare_hydrophobic
from modules.select_regions import set_drop_region, set_surface_line, correct_tilt, user_line, draw_rectangle, draw_line, optimized_path, intersection, ML_prepare_hydrophobic
from numpy.testing import assert_array_equal
from unittest.mock import patch, MagicMock



class TestSelectRegions(unittest.TestCase):

    @patch('modules.preprocessing.auto_crop')
    def test_set_drop_region_auto(self, mock_auto_crop):
        # Create mock return value
        mock_image = np.zeros((100, 100, 3))  # Simulate a blank image of size 100x100
        mock_auto_crop.return_value = (mock_image, (10, 90, 20, 80))  # Simulate cropping result

        # Simulate experimental_drop and experimental_setup objects
        experimental_drop = MagicMock()
        experimental_drop.image = mock_image
        experimental_setup = MagicMock()
        experimental_setup.drop_ID_method = "Automated"

        # Call the function to be tested
        set_drop_region(experimental_drop, experimental_setup)

        # Check if auto_crop was called correctly
        mock_auto_crop.assert_called_once_with(mock_image)

        # Verify if experimental_drop handled auto_crop's return value correctly
        self.assertTrue(np.array_equal(experimental_drop.cropped_image, mock_image))
        self.assertEqual(experimental_setup.drop_region, [(10, 20), (90, 80)])

    @patch('modules.select_regions.user_ROI')
    @patch('modules.select_regions.image_crop')
    def test_set_drop_region_user_selected(self, mock_image_crop, mock_user_ROI):
        # Create mock return value
        mock_image = np.zeros((100, 100, 3))  # Simulate a blank image of size 100x100
        mock_user_ROI.return_value = [(10, 20), (90, 80)]  # Simulate the user-selected region

        # Simulate the cropped image as a 3D array
        mock_cropped_image = np.zeros((60, 80, 3))  # Assume the cropped result is still 3D
        mock_image_crop.return_value = mock_cropped_image

        # Simulate experimental_drop and experimental_setup objects
        experimental_drop = MagicMock()
        experimental_drop.image = mock_image
        experimental_setup = MagicMock()
        experimental_setup.drop_ID_method = "User-selected"

        # Call the function to be tested
        set_drop_region(experimental_drop, experimental_setup)

        # Check if user_ROI was called correctly
        mock_user_ROI.assert_called_once_with(mock_image, 'Select drop region', unittest.mock.ANY, unittest.mock.ANY)

        # Verify if image_crop was called correctly
        mock_image_crop.assert_called_once_with(mock_image, [(10, 20), (90, 80)])

        # Check if experimental_drop and experimental_setup handled user_ROI's return value correctly
        self.assertEqual(experimental_setup.drop_region, [(10, 20), (90, 80)])
        self.assertEqual(experimental_drop.cropped_image.shape, (60, 80, 3))  # Verify the cropped image size


class TestSurfaceLine(unittest.TestCase):

    @patch('modules.select_regions.prepare_hydrophobic')
    @patch('modules.preprocessing.optimized_path')
    def test_set_surface_line_auto(self, mock_optimized_path, mock_prepare_hydrophobic):
        # Simulate optimized_path return value to ensure enough data points for distance calculation
        mock_optimized_path.return_value = np.array([[0, 0], [1, 2], [2, 4], [3, 6], [4, 8], [5, 10]])

        # Create mock return values
        mock_contour = np.array([[0, 0], [1, 2], [2, 4], [3, 6], [4, 8], [5, 10]])  # Using more contour points
        mock_contact_points = {0: [0, 0], 1: [5, 10]}
        mock_prepare_hydrophobic.return_value = (mock_contour, mock_contact_points)

        # Simulate experimental_drop and experimental_setup objects
        experimental_drop = MagicMock()
        experimental_drop.contour = mock_contour
        experimental_setup = MagicMock()
        experimental_setup.baseline_method = "Automated"

        # Call the function to be tested
        set_surface_line(experimental_drop, experimental_setup)

        # Check if prepare_hydrophobic was called correctly
        mock_prepare_hydrophobic.assert_called_once_with(mock_contour)

        # Verify if the return values were handled correctly
        self.assertTrue(np.array_equal(experimental_drop.drop_contour, mock_contour))
        self.assertEqual(experimental_drop.contact_points, mock_contact_points)


class TestCorrectTilt(unittest.TestCase):

    @patch('modules.select_regions.tilt_correction')
    def test_correct_tilt_auto(self, mock_tilt_correction):
        # Create mock return value
        mock_cropped_image = np.zeros((100, 100, 3))
        mock_tilt_correction.return_value = mock_cropped_image

        # Simulate experimental_drop and experimental_setup objects
        experimental_drop = MagicMock()
        experimental_drop.cropped_image = mock_cropped_image
        experimental_drop.contact_points = [(10, 20), (90, 80)]
        experimental_setup = MagicMock()
        experimental_setup.baseline_method = "Automated"

        # Call the function to be tested
        correct_tilt(experimental_drop, experimental_setup)

        # Check if tilt_correction was called correctly
        mock_tilt_correction.assert_called_once_with(mock_cropped_image, [(10, 20), (90, 80)])

        # Verify if the return values were handled correctly
        self.assertTrue(np.array_equal(experimental_drop.cropped_image, mock_cropped_image))


# class TestUserLine(unittest.TestCase):
#
#     @patch('modules.fits.perform_fits')  # Ensure correct function path
#     @patch('modules.select_regions.cv2.line')
#     @patch('modules.select_regions.cv2.imshow')
#     @patch('modules.select_regions.set_screen_position', return_value=(0, 0))  # Simulate screen resolution setting
#     def test_user_line(self, mock_set_screen_position, mock_imshow, mock_line, mock_perform_fits):
#         # Simulate input image and contour data
#         mock_image = np.zeros((100, 100, 3))  # A blank 100x100 image
#
#         # Simulate contour data to ensure a valid drop is generated
#         mock_contour = np.array([[10, 50], [20, 30], [30, 10], [40, 5], [50, 2]])
#         mock_contact_points = {0: [10, 50], 1: [50, 2]}  # Simulate contact points
#
#         # Simulate experimental_drop and experimental_setup objects
#         experimental_drop = MagicMock()
#         experimental_drop.cropped_image = mock_image
#         experimental_drop.contour = mock_contour
#         experimental_drop.contact_points = mock_contact_points
#
#         experimental_setup = MagicMock()
#         experimental_setup.screen_resolution = (1920, 1080)
#         experimental_setup.drop_region = np.array([[0, 0], [100, 100]])  # Simulate the region
#         experimental_setup.tangent_boole = True  # Enable tangent fitting
#         experimental_setup.second_deg_polynomial_boole = False
#         experimental_setup.circle_boole = False
#         experimental_setup.ellipse_boole = False
#
#         # Simulate a valid return value for the perform_fits function
#         mock_perform_fits.return_value = {
#             'tangent fit': {
#                 'tangent lines': [
#                     [[10, 50], [20, 40]],  # First tangent line
#                     [[40, 30], [50, 20]]  # Second tangent line
#                 ]
#             }
#         }
#
#         # Call the function to be tested
#         user_line(experimental_drop, experimental_setup)
#
#         # Check if perform_fits was called correctly
#         mock_perform_fits.assert_called_once_with(
#             experimental_drop, tangent=True, polynomial=False, circle=False, ellipse=False
#         )


class TestDrawRectangle(unittest.TestCase):

    @patch('modules.select_regions.cv2.rectangle')
    @patch.dict('modules.select_regions.__dict__', {'image_TEMP': np.zeros((100, 100, 3)), 'img': np.zeros((100, 100, 3))})
    def test_draw_rectangle(self, mock_rectangle):
        global drawing, ix, iy, fx, fy
        # Initialize local variables
        drawing = False
        ix, iy = 0, 0
        fx, fy = 0, 0

        # Simulate mouse button down event
        draw_rectangle(cv2.EVENT_LBUTTONDOWN, 10, 20, None, None)
        mock_rectangle.assert_not_called()  # No rectangle should be drawn when mouse is pressed down

        # Simulate mouse move event, cv2.rectangle should be called
        draw_rectangle(cv2.EVENT_MOUSEMOVE, 30, 40, None, None)
        called_args = mock_rectangle.call_args
        assert np.array_equal(called_args[0][0], np.zeros((100, 100, 3)))  # Manually compare numpy arrays
        assert called_args[0][1] == (10, 20)
        assert called_args[0][2] == (30, 40)
        assert called_args[0][3] == (0, 0, 255)
        assert called_args[0][4] == 2

        # Simulate mouse button release event, cv2.rectangle should be called again
        draw_rectangle(cv2.EVENT_LBUTTONUP, 50, 60, None, None)
        called_args = mock_rectangle.call_args
        assert np.array_equal(called_args[0][0], np.zeros((100, 100, 3)))  # Manually compare numpy arrays
        assert called_args[0][1] == (10, 20)
        assert called_args[0][2] == (50, 60)
        assert called_args[0][3] == (0, 255, 0)
        assert called_args[0][4] == 2


class TestDrawLine(unittest.TestCase):

    @patch('modules.select_regions.cv2.line')
    @patch.dict('modules.select_regions.__dict__', {'image_TEMP': np.zeros((100, 100, 3)), 'img': np.zeros((100, 100, 3))})
    def test_draw_line(self, mock_line):
        global drawing, ix, iy, fx, fy
        # Initialize local variables
        drawing = False
        ix, iy = 0, 0
        fx, fy = 0, 0

        # Simulate mouse button down event
        draw_line(cv2.EVENT_LBUTTONDOWN, 10, 20, None, None)
        mock_line.assert_not_called()  # No line should be drawn when mouse is pressed down

        # Simulate mouse move event, cv2.line should be called
        draw_line(cv2.EVENT_MOUSEMOVE, 30, 40, None, None)
        args, kwargs = mock_line.call_args
        assert_array_equal(args[0], np.zeros((100, 100, 3)))  # Compare first argument
        self.assertEqual(args[1], (10, 20))  # Compare start point
        self.assertEqual(args[2], (30, 40))  # Compare end point
        self.assertEqual(args[3], (0, 0, 255))  # Compare color
        self.assertEqual(args[4], 2)  # Compare line thickness

        # Simulate mouse button release event, cv2.line should be called again
        draw_line(cv2.EVENT_LBUTTONUP, 50, 60, None, None)
        args, kwargs = mock_line.call_args
        assert_array_equal(args[0], np.zeros((100, 100, 3)))  # Compare first argument
        self.assertEqual(args[1], (10, 20))  # Compare start point
        self.assertEqual(args[2], (50, 60))  # Compare end point
        self.assertEqual(args[3], (0, 255, 0))  # Compare color
        self.assertEqual(args[4], 2)  # Compare line thickness


class TestOptimizedPath(unittest.TestCase):

    def test_optimized_path_with_mock_distance(self):
        coords = [(0, 0), (1, 2), (3, 4), (5, 6)]
        start = (0, 0)

        # Use patch to mock the behavior of distance function
        with patch('modules.select_regions.distance', side_effect=cycle([1])) as mock_distance:
            result = optimized_path(coords, start)

            print("Distance call count:", mock_distance.call_count)  # Add debug output

            # Expected call count is 6 times
            self.assertEqual(mock_distance.call_count, 6)

    def test_optimized_path_without_start(self):
        coords = [(0, 0), (1, 2), (3, 4), (5, 6)]

        # Verify when start is not provided, it defaults to the first point
        result = optimized_path(coords)
        expected_result = np.array([(0, 0), (1, 2), (3, 4), (5, 6)])
        np.testing.assert_array_equal(result, expected_result)

    def test_optimized_path_with_single_point(self):
        coords = [(0, 0)]

        # Handle the case of a single point, the result should return the input single point
        result = optimized_path(coords)
        expected_result = np.array([(0, 0)])
        np.testing.assert_array_equal(result, expected_result)

# Before testing MLPrepareHydrophobic, modify line 518 in select_regions from "if 0" to "if True"
class TestMLPrepareHydrophobic(unittest.TestCase):

    # @patch('modules.select_regions.plt.plot')  # Mock the behavior of plt.plot
    # def test_ML_prepare_hydrophobic_plot_called(self, mock_plt_plot):
    #     # Simulate input data
    #     coords_in = np.array([
    #         [1, 2],
    #         [3, 4],
    #         [5, 6],
    #         [7, 8]
    #     ])
    #
    #     # Force execution of the plotting code block, directly call the function, no side_effect used
    #     result = ML_prepare_hydrophobic(coords_in)
    #
    #     # Verify if plt.plot was called correctly in the function
    #     self.assertTrue(mock_plt_plot.called)

    def test_ML_prepare_hydrophobic_np_delete_called(self):
        # Test if np.delete was called
        pass

    def test_ML_prepare_hydrophobic_return_shape(self):
        # Test if the return result shape is correct
        pass

if __name__ == '__main__':
    unittest.main()
