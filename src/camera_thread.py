#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This module constructs the live image stream to visualize the detection.
Uses a new thread and event to collaborate with PyQt framework.
"""

import os
import time

import numpy as np
from pypylon import pylon
from PyQt6.QtCore import QThread, pyqtSignal

from src.params import GRABBING_TIMEOUT_MS, ROOT_DIR


class CameraThread(QThread):
    """A QThread derived class to construct the live camera feed.

    Args:
        QThread (PyQt6.QtCore): Base class
    """

    # Signal to send the frame image, frame count, and timestamp to the UI
    frame_signal: pyqtSignal = pyqtSignal(np.ndarray, int, float)
    camera: pylon.InstantCamera

    def __init__(self, camera: pylon.InstantCamera) -> None:
        super().__init__()
        self.camera = camera

    def run(self) -> None:
        """
        The main function to run the camera feed.
        Overwrites the run method of QThread.
        """
        converter: pylon.ImageFormatConverter = pylon.ImageFormatConverter()

        # Converting to opencv bgr format
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        # Explicitly declaring an array helps reducing processing time in blocking polling loop
        grab_result: pylon.GrabResult
        pylon_image: pylon.PylonImage
        image: np.ndarray[np.uint8]
        grab_time: float

        self.camera.Open()

        if os.environ['PYLON_CAMEMU'] == '1':
            # Disable standard test images
            self.camera.TestImageSelector.Value = "Off"
            # Enable custom test images
            self.camera.ImageFileMode.Value = "On"
            # Load custom test images in specified directory from disk
            self.camera.ImageFilename.Value = f"{ROOT_DIR}\\backup\\AAA\\Figs\\"

        # Only grab the latest image
        # Blocks till the image is processed
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

        count = 0
        # Loop until the camera stops grabbing, throws an exception or an interruption is requested
        while self.camera.IsGrabbing() and not self.isInterruptionRequested():
            # Obtain the latest frame and process it
            # timeoutMs: 5000
            # timeoutHandling: pylon.TimeoutHandling_ThrowException
            grab_result = self.camera.RetrieveResult(
                GRABBING_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                pylon_image = converter.Convert(grab_result)
                image = pylon_image.GetArray()
                grab_time = time.time()
                self.frame_signal.emit(image, count, grab_time)
                count += 1

            grab_result.Release()

        self.camera.StopGrabbing()
        self.camera.Close()
