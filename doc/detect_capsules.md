### Detect Capsule in an Image

To detect capsule-shaped objects in an image using OpenCV in Python, follow these steps:

1. **reprocess the Image**

   - Convert the image to grayscale.
   - Apply Gaussian blur to reduce noise.
   - Use edge detection (like the Canny edge detector) to identify object outlines.

2. **Find Contours**

   - Use `cv2.findContours()` to detect contours in the processed image.
   - Approximate each contour’s shape using `cv2.approxPolyDP()`.

3. **Analyze Shapes**

   - For each contour, fit an ellipse using `cv2.fitEllipse()` if the contour has enough points.
   - Measure the aspect ratio (major axis divided by minor axis) of the ellipse.
   - Filter out objects that do not match the expected aspect ratio of capsules (e.g., elongated shapes with aspect ratios between 2.0 and 5.0).

4. **Highlight Capsules**
   - Draw the detected capsules on the image using `cv2.ellipse()` or `cv2.drawContours()`.
