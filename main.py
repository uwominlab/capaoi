#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This is the entry point for the application.
Using type hints to reduces compilation time and save run time resources.
"""


import time

import cv2
import numpy as np
from pypylon import pylon

from src.params import INIT_EXPOSURE_TIME, INIT_FRAME_RATE, INIT_GAIN, \
    INIT_WIDTH, INIT_HEIGHT, GRABBING_TIMEOUT_MS


def main() -> None:
    """
    Main function to run the application.
    """
    # Create an instance of the camera object.
    camera: pylon.InstantCamera = pylon.InstantCamera(
        pylon.TlFactory.GetInstance().CreateFirstDevice()
    )
    camera.Open()

    # Set camera related paramters
    camera.ExposureTime.Value = INIT_EXPOSURE_TIME
    camera.AcquisitionFrameRate.SetValue(INIT_FRAME_RATE)
    camera.Gain.SetValue(INIT_GAIN)

    camera.Width.SetValue(INIT_WIDTH)
    camera.Height.SetValue(INIT_HEIGHT)

    camera.StopGrabbing()
    # Only grab the latest image
    # Blocks till the image is processed
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    # image: np.ndarray
    # shape = (nrows, ncols)
    # Explicitly declaring an array helps reducing processing time in blocking polling loop
    image: np.ndarray = np.empty(shape=(INIT_HEIGHT, INIT_WIDTH))

    count: int = 0
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
