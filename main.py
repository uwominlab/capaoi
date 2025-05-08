#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This is the entry point for the application.
Using type hints to reduces compilation time and save run time resources.
"""


import logging
import os
import sys

import cv2

# pylint: disable=no-name-in-module
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from src.params import ROOT_DIR
from src.main_window import MainWindow

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
MASK_BIN: cv2.typing.MatLike = cv2.imread(MASK_IMG_PATH, cv2.IMREAD_GRAYSCALE)


def main() -> None:
    """
    Main function to run the application.
    """

    # Create singleton project settings node
    settings: QSettings = QSettings("MinLab", "CapAOI")
    settings.setValue("camera/debug", True)
    settings.setValue("defect/debug", True)
    settings.setValue("relay2/debug", True)

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
