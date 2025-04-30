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
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from src.contours import find_contours_img
from src.defects import detect_capsule_defects

from src.params import BELT_LENGTH_MM, BELT_SPEED_MM_S
from src.params import GRABBING_TIMEOUT_MS, INIT_EXPOSURE_TIME, INIT_FRAME_RATE, INIT_GAIN
from src.params import INIT_HEIGHT, INIT_WIDTH, MM_PER_PIXEL
# from src.params import ACTUATOR_RETRACTION_TIME
from src.params import ROOT_DIR

from src.main_window import MainWindow
# from src.relay_controller import RelayController

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
MASK_IMG_PATH: str = os.path.join(
    ROOT_DIR, "data", "Figs_14", "Capsule_1_mask_binary.png")
# pylint: disable=no-member
# MASK_RAW: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH)
MASK_BIN: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH, cv2.IMREAD_GRAYSCALE)

if USE_EMULATION:
    os.environ['PYLON_CAMEMU'] = '1'


def main() -> None:
    """
    Main function to run the application.
    """

    # Create singleton project settings node
    settings: QSettings = QSettings("MinLab", "CapAOI")
    settings.setValue("camera/debug", True)
    settings.setValue("defect/debug", True)
    settings.setValue("relay1/debug", True)

    # Create the main window and run the application
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("Capsule Defects Detection")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("The University of Western Ontario")
    app.setOrganizationDomain("uwo.ca")
    window: MainWindow = MainWindow()
    window.resize(1280, 940)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
