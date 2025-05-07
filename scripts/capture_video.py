from pypylon import pylon
import cv2
import time
import os

# === Settings ===
output_dir = "captured_frames"
video_output_path = "output_video.avi"
frame_rate = 10  # frames per second
duration_sec = 10
save_as_video = True

# === Prepare Output ===
os.makedirs(output_dir, exist_ok=True)
num_frames = frame_rate * duration_sec

# === Connect to Camera ===
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# === Camera Configuration ===
camera.PixelFormat = "Mono8"
camera.AcquisitionFrameRateEnable.SetValue(True)
camera.AcquisitionFrameRate.SetValue(frame_rate)
camera.ExposureTime.SetValue(20000)  # in microseconds

# === Start Grabbing ===
camera.StartGrabbingMax(num_frames, pylon.GrabStrategy_LatestImageOnly)

# === Video Writer (Optional) ===
video_writer = None
if save_as_video:
    width = camera.Width.Value
    height = camera.Height.Value
    video_writer = cv2.VideoWriter(
        video_output_path, cv2.VideoWriter_fourcc(*'XVID'), frame_rate, (width, height), isColor=False
    )

# === Capture Loop ===
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_Mono8
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

frame_idx = 0
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
