#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This is the entry point for the application.
Using type hints to reduces compilation time and save run time resources.
"""


import logging
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from pypylon import pylon

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QApplication

from src.contours import find_contours_img
from src.defects import detect_capsule_defects

from src.params import BELT_LENGTH_MM, BELT_SPEED_MM_S
from src.params import GRABBING_TIMEOUT_MS, INIT_EXPOSURE_TIME, INIT_FRAME_RATE, INIT_GAIN
from src.params import INIT_HEIGHT, INIT_WIDTH, MM_PER_PIXEL
from src.params import ACTUATOR_RETRACTION_TIME
from src.params import ROOT_DIR

from src.main_window import MainWindow
from src.relay_controller import RelayController

from utils.transform import get_img_opened
from utils.visualize import cvimshow


# Change this to False for release mode
DEBUG_MODE: bool = True
USE_EMULATION: bool = False

# Set logging level based on a debug flag
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize the constant variables
MASK_IMG_PATH: str = os.path.join(ROOT_DIR, "data", "Figs_14", "000_mask_raw.png")
# pylint: disable=no-member
MASK_RAW: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH)
MASK_BIN: cv2.typing.MatLike = get_img_opened(MASK_RAW)

if USE_EMULATION:
    os.environ['PYLON_CAMEMU'] = '1'


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def main() -> None:
    """
    Main function to run the application.
    """
    # Create an instance of the camera object
    try:
        camera: pylon.InstantCamera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        logging.debug(camera.GetDeviceInfo().GetFriendlyName())
    except (pylon.GenericException, RuntimeError) as e:
        logging.error("Error retrieving frame %s", e)

    camera.Open()

    # Set camera related paramters
    camera.ExposureTime.Value = INIT_EXPOSURE_TIME
    camera.AcquisitionFrameRateEnable.Value = True
    camera.AcquisitionFrameRate.SetValue(INIT_FRAME_RATE)
    camera.AcquisitionMode.SetValue("Continuous")
    camera.Gain.SetValue(INIT_GAIN)

    camera.Width.SetValue(INIT_WIDTH)
    camera.Height.SetValue(INIT_HEIGHT)

    # Set the X axis offset such that it only looks at the horizontal centric pixels
    camera.OffsetX.Value = (camera.Width.GetMax() - INIT_WIDTH) // 2
    # Set the Y axis offset such that it only looks at the vertical centric pixels
    camera.OffsetY.Value = (camera.Height.GetMax() - INIT_HEIGHT) // 2

    # Retreive sensor width and height, and convert µm to mm
    sensor_width_mm: float = camera.SensorWidth.GetValue() / 1000.0
    sensor_height_mm: float = camera.SensorHeight.GetValue() / 1000.0

    logging.debug(
        "Sensor Size: %.2f mm x %.2f mm", sensor_width_mm, sensor_height_mm)

    if 'PYLON_CAMEMU' in os.environ and os.environ['PYLON_CAMEMU'] == '1':
        # Disable standard test images
        camera.TestImageSelector.Value = "Off"
        # Enable custom test images
        camera.ImageFileMode.Value = "On"
        # Load custom test images in specified directory from disk
        camera.ImageFilename.Value = f"{ROOT_DIR}\\backup\\AAA\\Figs\\"
    else:
        temp = camera.BslTemperatureStatus.Value

    camera.StopGrabbing()
    # Only grab the latest image
    # Blocks till the image is processed
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    converter: pylon.ImageFormatConverter = pylon.ImageFormatConverter()

    # Converting to opencv bgr format
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    # Explicitly declaring an array helps reducing processing time in blocking polling loop
    grab_result: pylon.GrabResult
    pylon_image: pylon.PylonImage
    image: np.ndarray[np.uint8]
    capsule_centers_abnormal: list[tuple[int, int]]

    abs_actuation_timestamps: list[float] = []
    relay_controller: RelayController = RelayController()

    # Loop until the camera stops grabbing and throws an exception
    while camera.IsGrabbing():
        # Obtain the latest frame and process it
        # timeoutMs: 5000
        # timeoutHandling: pylon.TimeoutHandling_ThrowException
        grab_result: pylon.GrabResult = camera.RetrieveResult(
            GRABBING_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            pylon_image = converter.Convert(grab_result)
            image = pylon_image.GetArray()

            # Image is a 2D matrix (2-channel image), not a traditional cv2.typing.MatLike
            if isinstance(image, np.ndarray) and image.shape[-1] == 2:
                # Extract first channel
                image = image[:, :, 0]
                # Convert to RGB
                # pylint: disable=no-member
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

            # Obtain the processed copy of the image
            img_opened: cv2.typing.MatLike = get_img_opened(image)

            # Find the contours in the image
            _, capsule_set_raw, capsule_set_opened, _, \
                capsule_centers, capsule_size, capsule_area, capsule_similarity = find_contours_img(
                    image, img_opened, MASK_BIN)

            # Detect the defective capsules
            capsule_centers_abnormal = detect_capsule_defects(
                capsule_set_raw, capsule_set_opened, capsule_centers,
                capsule_size, capsule_area, capsule_similarity)

            # Get current timestamp in seconds
            current_time_s: float = time.time()

            # Calculate absolute actuation timestamps
            abs_actuation_timestamps += [
                current_time_s +
                ((INIT_WIDTH - center[0]) * MM_PER_PIXEL +
                 BELT_LENGTH_MM) / BELT_SPEED_MM_S
                for center in capsule_centers_abnormal
            ]

            # Check if the relay should be actuated by
            # comparing the current time with the actuation timestamps
            if abs_actuation_timestamps and \
                    min(abs_actuation_timestamps) <= current_time_s <= max(abs_actuation_timestamps):
                relay_controller.turn_on(relay_number=RELAY_1)
                # Remove the executed timestamp
                abs_actuation_timestamps.pop(0)
            else:
                relay_controller.turn_off(relay_number=RELAY_1)

            abs_actuation_timestamps = [
                timestamp for timestamp in abs_actuation_timestamps if timestamp >= current_time_s]

            if abs_actuation_timestamps and \
                current_time_s + ACTUATOR_RETRACTION_TIME < min(abs_actuation_timestamps):
                relay_controller.turn_off(relay_number=RELAY_1)

            # Assertions and visualization
            if DEBUG_MODE:
                if not USE_EMULATION:
                    assert image is not None
                    assert image.ndim == 3
                    assert image.shape == (INIT_HEIGHT, INIT_WIDTH, 3)

                points: list[tuple[int, int]] = [
                    (int(x), int(y)) for x, y in capsule_centers
                ]
                for index, point in enumerate(points):
                    # Draw a green filled circle
                    cv2.putText(
                        img=image, text=str(index), org=(point[0], point[1]),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=2, color=(255, 0, 0), thickness=2)

                points = [(int(x), int(y))
                          for x, y in capsule_centers_abnormal]
                for index, point in enumerate(points):
                    # Draw a red filled circle
                    cv2.circle(
                        img=image, center=point, radius=5,
                        color=(0, 0, 255), thickness=5)

                cvimshow("Defects Dectection Results", image)

            # press 'ESC' to exit the loop
            key = cv2.waitKey(1)
            if key == 27:
                break

        grab_result.Release()

    # Close the camera and release resources
    camera.StopGrabbing()
    camera.Close()
    relay_controller.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
