#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This module constructs the live image stream to visualize the detection.
Uses a new thread and event to collaborate with PyQt framework.
"""

import logging
import time

import numpy as np
from pypylon import pylon
from PyQt6.QtCore import QThread, pyqtSignal

from src.params import GRABBING_TIMEOUT_MS


class CameraFeed(QThread):
    """A QThread derived class to construct the live camera feed.

    Args:
        QThread (PyQt6.QtCore): Base class
    """

    # Signal to send the frame image, frame count, and timestamp to the UI
    frame_signal: pyqtSignal = pyqtSignal(np.ndarray, int, float)
    camera: pylon.InstantCamera

    def __init__(self, camera: pylon.InstantCamera) -> None:
        self.camera = camera

    def run(self) -> None:
        self.camera.Open()

        # Start grabbing using the latest image strategy
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        count = 0
        while self.camera.IsGrabbing() and not self.isInterruptionRequested():
            grab_result: pylon.GrabResult = self.camera.RetrieveResult(
                GRABBING_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                image = grab_result.Array
                grab_time = time.time()
                self.frame_signal.emit(image, count, grab_time)
                count += 1

            grab_result.Release()

        self.camera.StopGrabbing()
        self.camera.Close()
