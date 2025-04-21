
"""
Unit tests for the `update_defects_detection_params` method in the `MainWindow` class.
"""

import unittest
from unittest.mock import MagicMock

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from src.main_window import MainWindow
from src.parameter import DefectDetectionParams


class TestUpdateDefectsDetectionParams(unittest.TestCase):
    """
    Unit tests for the `update_defects_detection_params` method in the `MainWindow` class.

    This test verifies that the defect detection parameters are updated correctly 
    when values are modified in the `QTableWidget`.

    Test Cases:
        - Test that the initial value of `normal_length_lower` is correct.
        - Test that updating the value through `update_defects_detection_params`
          changes the parameter correctly.
    
    Attributes:
        params (DefectDetectionParams): `DefectDetectionParams` containing test parameters.
        window (MockMainWindow): Mocked `MainWindow` with a real `QTableWidget` for testing.
    """
    @classmethod
    def setUpClass(cls):
        """
        Sets up the QApplication instance required for PyQt6 tests.
        """
        cls.app = QApplication([])

    def setUp(self):
        """
        Sets up the test environment.

        This includes:
            - Creating an instance of `DefectDetectionParams` with test values.
            - Creating a mock version of `MainWindow`.
            - Setting up a real `QTableWidget` for compatibility with `QSignalBlocker`.
            - Binding `update_defects_detection_params` to the mock instance.
        """
        self.params = DefectDetectionParams(
            normal_length_lower=10,
            normal_length_upper=50,
            normal_area_lower=20,
            normal_area_upper=100,
            similarity_threshold=0.8,
            local_defect_length=15
        )

        class MockMainWindow:
            """
            A mock version of `MainWindow` used for testing.

            Args:
                params (DefectDetectionParams): Initial defect detection parameters.
            """
            def __init__(self, params):
                super().__init__()
                self.detection_params = params
                self.camera_thread = MagicMock()

                # Use a real QTableWidget to avoid QSignalBlocker issues
                self.capsule_param_table = QTableWidget(3, 3)
                self.capsule_param_table.setItem(
                    0, 0, QTableWidgetItem("Contour length threshold TL (pixel)"))

        self.window = MockMainWindow(self.params)

        def update_defects_detection_params_wrapper(item: QTableWidgetItem) -> None:
            """
            Wrapper for the `update_defects_detection_params` method.

            This allows testing the method without directly inheriting from `MainWindow`.

            Args:
                item (QTableWidgetItem): The table item that was modified.
            """
            MainWindow.update_defects_detection_params(self.window, item)

        self.window.update_defects_detection_params = update_defects_detection_params_wrapper

    def test_update_defects_detection_params(self):
        """
        Tests that the `update_defects_detection_params` method correctly updates
        the `normal_length_lower` parameter when the table value is modified.
        """
        self.assertEqual(self.window.detection_params.normal_length_lower, 10)
        item = QTableWidgetItem("30")
        self.window.capsule_param_table.setItem(0, 1, item)
        self.window.capsule_param_table.setItem(0, 2, QTableWidgetItem("60"))
        self.window.update_defects_detection_params(item)
        self.assertEqual(self.window.detection_params.normal_length_lower, 30)

    @classmethod
    def tearDownClass(cls):
        """
        Cleans up the QApplication instance after all tests are complete.
        """
        cls.app.quit()


if __name__ == "__main__":
    unittest.main()
