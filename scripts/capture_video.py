"""
Capture video from a Basler camera and save frames to disk or as a video file.
This script uses the pypylon library to interface with Basler cameras and OpenCV to handle image processing and saving.
"""

from pypylon import pylon
import cv2
import time
import os

# === Settings ===
output_dir: str = "captured_frames"
video_output_path: str = "output_video.avi"
frame_rate: int = 15  # frames per second
duration_sec: int = 5  # duration of the capture in seconds
width: int = 2160  # width of the image in pixels
height: int = 1440  # height of the image in pixels
save_as_video = False  # set to True to save as video

# === Prepare Output ===
os.makedirs(output_dir, exist_ok=True)
num_frames = frame_rate * duration_sec

# === Connect to Camera ===
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# === Camera Configuration ===
camera.UserSetSelector.SetValue("Default")
camera.UserSetLoad.Execute()
camera.AcquisitionFrameRateEnable.SetValue(True)
camera.AcquisitionFrameRate.SetValue(frame_rate)
camera.AcquisitionMode.SetValue("Continuous")
camera.Width.SetValue(width)
camera.Height.SetValue(height)
# Set the X axis offset such that it only looks at the horizontal centric pixels
camera.OffsetX.SetValue((camera.Width.GetMax() - width) // 2)
# Set the Y axis offset such that it only looks at the vertical centric pixels
camera.OffsetY.SetValue((camera.Height.GetMax() - height) // 2)

# === Video Writer (Optional) ===
video_writer: cv2.VideoWriter = cv2.VideoWriter()
if save_as_video:
    width = camera.Width.Value
    height = camera.Height.Value
    video_writer = cv2.VideoWriter(
        video_output_path, cv2.VideoWriter_fourcc(*'XVID'), frame_rate, (width, height), isColor=False
    )
# === Start Grabbing ===
camera.StartGrabbingMax(num_frames, pylon.GrabStrategy_LatestImageOnly)

# === Capture Loop ===
converter: pylon.ImageFormatConverter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

frame_idx: int = 0
while camera.IsGrabbing():
    grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grab_result.GrabSucceeded():
        image = converter.Convert(grab_result)
        frame = image.GetArray()

        # Save image
        frame_path = os.path.join(output_dir, f"frame_{frame_idx:04d}.png")
        cv2.imwrite(frame_path, frame)

        # Write to video
        if save_as_video:
            video_writer.write(frame)

        frame_idx += 1

    grab_result.Release()

# === Cleanup ===
camera.StopGrabbing()
camera.Close()

if video_writer:
    video_writer.release()

print(f"Finished capturing {frame_idx} frames.")
