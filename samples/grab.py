"""
Demonstrates how to grab images from a camera using the pypylon library.
"""

import numpy
from pypylon import pylon

camera: pylon.InstantCamera = pylon.InstantCamera(
    pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

assert camera.Width.Inc == 4

# demonstrate some feature access
new_width = camera.Width.Value - camera.Width.Inc
if new_width >= camera.Width.Min:
    camera.Width.Value = new_width

numberOfImagesToGrab: int = 5  # 100
camera.StartGrabbingMax(numberOfImagesToGrab)

while camera.IsGrabbing():
    grabResult: pylon.GrabResult = camera.RetrieveResult(
        5000, pylon.TimeoutHandling_ThrowException)

    print("Type of grabResult: ", type(grabResult))

    if grabResult.GrabSucceeded():
        # Access the image data
        print("SizeX: ", grabResult.Width)
        print("SizeY: ", grabResult.Height)

        # Obtain the pixel array
        img: numpy.ndarray = grabResult.Array
        print("Gray value of first pixel: ", img[0, 0])
        print("Type of img: ", type(img))
        print("Number of dimension: ", img.ndim)

    grabResult.Release()
camera.Close()
