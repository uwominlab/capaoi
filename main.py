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

import cv2
import numpy as np
from pypylon import pylon

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QApplication

from src.contours import find_contours_img
from src.defects import detect_capsule_defects
from src.params import (
    BELT_LENGTH_MM, BELT_SPEED_MM_S, GRABBING_TIMEOUT_MS,
    INIT_EXPOSURE_TIME, INIT_FRAME_RATE, INIT_GAIN,
    INIT_HEIGHT, INIT_WIDTH, MM_PER_PIXEL, RELAY_1, ACTUATOR_RETRACTION_TIME, ROOT_DIR)

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
MASK_IMG_PATH: str = "./data/Figs_14/000_mask_raw.png"
MASK_RAW: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH)  # pylint: disable=no-member
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

    # Loop until the camera stops grabbing and throws an exception
    while camera.IsGrabbing():
        # Obtain the latest frame and process it
        # timeoutMs: 5000
        # timeoutHandling: pylon.TimeoutHandling_ThrowException
        grab_result: pylon.GrabResult = camera.RetrieveResult(
            GRABBING_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            image = grab_result.Array

            assert image is not None
            assert image.ndim == 2
            assert image.shape == (INIT_HEIGHT, INIT_WIDTH)

            grab_time: float = time.time()

            # TODO: detect if there are defects in capsules
            # is_fault,fault_coord = defect_diagnose(image)
            process_time: float = time.time()

            # while is_fault:
            #     for coord in fault_coord:
            #         delay_time = (conveyer_len+coord)/conveyer_rate - (process_time-grab_time) + calib_time
            #         threading.Thread(target=start_blowing, args=(client, output_address, delay_time), daemon=True).start()
            cv2.imshow(winname="Processed Image", mat=image)

            print(count)
            count += 1

            # press 'ESC' to exit the loop
            key = cv2.waitKey(1)
            if key == 27:
                break

        grab_result.Release()

    # Close the camera and release resources
    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
