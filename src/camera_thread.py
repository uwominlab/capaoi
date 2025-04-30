#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This module constructs the live image stream to visualize the detection.
Uses a new thread and event to collaborate with PyQt framework.
"""

import logging
import os
import time

import cv2
import numpy as np
from numpy.typing import NDArray
from pypylon import pylon
# pylint: disable=no-name-in-module
from PyQt6.QtCore import QSettings, QThread, pyqtSignal

from src.contours import find_contours_img
from src.defects import detect_capsule_defects

from src.parameter import DefectDetectionParams

from src.params import ROOT_DIR
from src.params import INIT_WIDTH, INIT_HEIGHT, INIT_FRAME_RATE
from src.params import INIT_GAIN, INIT_EXPOSURE_TIME, GRABBING_TIMEOUT_MS
from src.params import MM_PER_PIXEL, BELT_LENGTH_MM, BELT_SPEED_MM_S

from utils.transform import remove_background, get_img_opened
from utils.visualize import cvimshow

# Change this to False for release mode
settings: QSettings = QSettings("MinLab", "CapAOI")
CAMERA_DEBUG: bool = settings.value(
    "camera/debug", type=bool, defaultValue=False)

# Set logging level based on a debug flag
logging.basicConfig(
    level=logging.DEBUG if CAMERA_DEBUG else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize the constant variables
MASK_IMG_PATH: str = os.path.join(
    ROOT_DIR, "data", "Figs_14", "Capsule_1_mask_binary.png")
# pylint: disable=no-member
# MASK_RAW: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH, cv2.IMREAD_UNCHANGED)
MASK_BIN: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH, cv2.IMREAD_GRAYSCALE)


class CameraThread(QThread):
    """
    A QThread derived class to construct the live camera feed.

    Args:
        QThread (PyQt6.QtCore): Base class

    Example:
    >>> from PyQt6.QtCore import QCoreApplication
    >>> import sys
    >>> app = QCoreApplication(sys.argv)
    >>> thread = CameraThread()
    >>> thread.isRunning()
    False
    >>> thread.start()
    >>> thread.isRunning()
    True
    >>> thread.quit()
    >>> thread.wait()
    >>> thread.isRunning()
    False
    """

    # Signal to send the frame image, frame count, and timestamp to the UI
    frame_signal: pyqtSignal = pyqtSignal(np.ndarray, int, float, float)
    frame_count: int = 0

    # Signal to send the timestamp to actuate the relay
    relay_signal: pyqtSignal = pyqtSignal(list)

    camera: pylon.InstantCamera
    camera_temperature_signal: pyqtSignal = pyqtSignal(str)

    detection_params: DefectDetectionParams = DefectDetectionParams()
    # Feedback signal to main window
    param_update_signal: pyqtSignal = pyqtSignal(DefectDetectionParams)

    def __init__(self, params: DefectDetectionParams) -> None:
        super().__init__()
        self.detection_params = params
        self.frame_count = 0
        # Create an instance of the camera camera_threadect
        try:
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice())
            logging.debug(self.camera.GetDeviceInfo().GetFriendlyName())
        except (pylon.GenericException, RuntimeError) as e:
            logging.error("Error retrieving frame %s", e)

        try:
            self.camera.Open()
        except UnboundLocalError as e:
            logging.error("Error opening camera %s", e)

        # Set camera related paramters
        self.camera.UserSetSelector.SetValue("Default")
        self.camera.UserSetLoad.Execute()
        # self.camera.ExposureTimeMode.SetValue("Common")
        # self.camera.ExposureTime.SetValue(INIT_EXPOSURE_TIME)
        self.camera.AcquisitionFrameRateEnable.SetValue(True)
        self.camera.AcquisitionFrameRate.SetValue(INIT_FRAME_RATE)
        self.camera.AcquisitionMode.SetValue("Continuous")
        # self.camera.Gain.SetValue(INIT_GAIN)
        self.camera.Width.SetValue(INIT_WIDTH)
        self.camera.Height.SetValue(INIT_HEIGHT)
        # Set the X axis offset such that it only looks at the horizontal centric pixels
        self.camera.OffsetX.SetValue(
            (self.camera.Width.GetMax() - INIT_WIDTH) // 2)
        # Set the Y axis offset such that it only looks at the vertical centric pixels
        self.camera.OffsetY.SetValue(
            (self.camera.Height.GetMax() - INIT_HEIGHT) // 2)
        self.camera.Close()

    # pylint: disable=too-many-locals
    def run(self) -> None:
        """
        The main function to run the camera feed.
        Overwrites the run method of QThread.
        """

        converter: pylon.ImageFormatConverter = pylon.ImageFormatConverter()

        # The output pixel format for the converter
        # The default pixel format is RGB8packed
        # Converting to opencv bgr format
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        # Explicitly declaring an array helps reducing processing time in blocking polling loop
        grab_result: pylon.GrabResult
        pylon_image: pylon.PylonImage
        image: NDArray[np.uint8]
        grab_time: float
        capsule_centers_abnormal: list[tuple[int, int]]
        abs_actuation_timestamps: list[float] = []

        self.camera.StopGrabbing()
        # Only grab the latest image
        # Blocks till the image is processed
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

        # Loop until the camera stops grabbing, throws an exception or an interruption is requested
        while self.camera.IsGrabbing() and not self.isInterruptionRequested():
            self.camera_temperature_signal.emit(
                self.camera.BslTemperatureStatus.GetValue())

            # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            # Obtain the latest frame and process it
            # timeoutMs: 5000
            # timeoutHandling: pylon.TimeoutHandling_ThrowException
            grab_result = self.camera.RetrieveResult(
                GRABBING_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                pylon_image = converter.Convert(grab_result)
                image = pylon_image.GetArray()

                # Remove background colour
                bgc_ranges: dict[str, tuple[list[int], list[int]]] = {
                    "bgc": ([0, 30, 60], [120, 190, 220])
                }
                image = remove_background(image, bgc_ranges)

                # Obtain the morphologically processed copy of the image
                image_opened: cv2.typing.MatLike = get_img_opened(image)

                # Find the contours in the image
                capsule_set_raw, capsule_set_opened, \
                    capsule_centers, capsule_size, capsule_area, capsule_similarity \
                    = find_contours_img(image, image_opened, MASK_BIN)

                # Detect the defective capsules
                capsule_centers_abnormal = detect_capsule_defects(
                    capsule_images_raw=capsule_set_raw,
                    capsule_masks=capsule_set_opened,
                    capsule_centers=capsule_centers,
                    capsule_sizes=capsule_size,
                    capsule_areas=capsule_area,
                    capsule_similarities=capsule_similarity,
                    normal_length_range=(
                        self.detection_params.normal_length_lower,
                        self.detection_params.normal_length_upper
                    ),
                    normal_width_range=(100, 150),
                    normal_area_range=(
                        self.detection_params.normal_area_lower,
                        self.detection_params.normal_area_upper
                    ),
                    similarity_threshold_overall=self.detection_params.similarity_threshold_overall,
                    similarity_threshold_head=0.3,
                    local_defect_length=self.detection_params.local_defect_length
                )

                # Get current timestamp in seconds
                grab_time = time.time()

                # Calculate absolute actuation timestamps
                abs_actuation_timestamps = [
                    grab_time +
                    ((INIT_WIDTH - center[0]) * MM_PER_PIXEL +
                     BELT_LENGTH_MM) / BELT_SPEED_MM_S
                    for center in capsule_centers_abnormal
                ]
                self.relay_signal.emit(abs_actuation_timestamps)

                points: list[tuple[int, int]] = [
                    (int(x), int(y)) for x, y in capsule_centers
                ]
                for index, point in enumerate(points):
                    cv2.putText(
                        img=image, text=str(index), org=(point[0], point[1]),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        # Draw a green filled circle
                        fontScale=2, color=(255, 0, 0), thickness=2)

                points = [(int(x), int(y))
                          for x, y in capsule_centers_abnormal]
                for index, point in enumerate(points):
                    cv2.circle(
                        img=image, center=point, radius=5,
                        # Draw a red filled circle
                        color=(0, 0, 255), thickness=5)

                self.frame_count += 1
                self.frame_signal.emit(
                    image, self.frame_count, grab_time, self.camera.ResultingFrameRate.GetValue())

            grab_result.Release()

        self.camera.StopGrabbing()
        self.camera.Close()

    def stop(self) -> None:
        """
        Stops the camera feed by interrupting the thread and closing the camera connection.

        This method:
        - Requests the thread to stop.
        - Waits for the thread to finish execution.
        - Stops the camera from grabbing new frames.
        - Closes the camera connection.
        """
        self.frame_count = 0
        self.requestInterruption()
        self.wait()
        self.camera.StopGrabbing()
        self.camera.Close()

    def set_detection_params(self, params: DefectDetectionParams) -> None:
        """
        Set the defect detection parameters.

        This method updates the internal defect detection parameters used by the AOI system.

        Args:
            params (DefectDetectionParams): An instance of `DefectDetectionParams` containing
                the configuration for defect detection.

        Returns:
            None

        Example:
            >>> class MockParams:
            ...     threshold = 0.8
            ...     max_defects = 5
            >>> params = MockParams()
            >>> camera_thread = CameraThread()
            >>> camera_thread.set_detection_params(params)
            >>> camera_thread.detection_params.threshold
            0.8
            >>> camera_thread.detection_params.max_defects
            5
        """
        self.detection_params = params


if __name__ == "__main__":
    import doctest
    doctest.testmod()
