import cv2
import numpy as np

SCALE_X: float = 0.25  # Scale factor for width
SCALE_Y: float = 0.25  # Scale factor for height

# Load the image
image: np.ndarray = cv2.imread(filename='data/Figs_14/006.bmp')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Preprocessing
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 50, 150)

# cv2.imshow(winname='Edges', mat=edges)

# Find contours
contours, _ = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

th3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY, 11, 2)
th3 = cv2.resize(th3, None, fx=SCALE_X, fy=SCALE_Y)
cv2.imshow(winname='Adaptive Gaussian', mat=th3)

# Analyze contours
for contour in contours:
    # Approximate the contour
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # Fit an ellipse if the contour has enough points
    if len(approx) > 5:
        ellipse = cv2.fitEllipse(contour)
        # MA and ma are the major and minor axes
        (x, y), (MA, ma), angle = ellipse
        aspect_ratio = max(MA, ma) / min(MA, ma)

        # Filter for capsule-like objects
        if 1.5 < aspect_ratio < 10.0:  # Adjust aspect ratio range based on your data
            cv2.ellipse(image, ellipse, (0, 255, 0), 2)

    # Check if it is a rectangle (4 vertices)
    elif len(approx) == 4:
        # Draw the rectangle on the original image
        cv2.drawContours(image, [approx], 0, (0, 255, 0), 3)


# Resize the output
resized_image = cv2.resize(image, None, fx=SCALE_X, fy=SCALE_Y)

# Display the result
cv2.imshow(winname='Resized Image of Detected Capsules', mat=resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
