# %%

import cv2
from matplotlib import pyplot as plt
import numpy as np

from utils.transform import preprocess_image

# %%
# Load the image
image: np.ndarray = cv2.imread(filename='data/Figs_14/006.bmp')

# Preprocess the image
processed_image: np.ndarray = preprocess_image(image)

# %%
print(type(image))
print(type(processed_image))

# Get image dimension
# Only take height and width, ignore channels
height, width = image.shape[:2]

print(f"Width: {width}, Height: {height}")

# %%
# Show the result
# Uncomment the following lines to see the over-sized image
# cv.imshow('Processed Image', processed_image)
# cv.waitKey(0)
# cv.destroyAllWindows()

# %%
scale_x: float = 0.25  # Scale factor for width
scale_y: float = 0.25  # Scale factor for height
resized_image = cv2.resize(processed_image, None, fx=scale_x, fy=scale_y)

cv2.imshow(winname='Resized Image', mat=resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# %%
# image: np.ndarray = cv2.imread(filename='../data/Figs_14/006.bmp')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Preprocessing
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges: cv2.typing.MatLike = cv2.Canny(blur, 50, 150)

# Find contours
contours, _ = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
        if 2.0 < aspect_ratio < 5.0:  # Adjust aspect ratio range based on your data
            cv2.ellipse(image, ellipse, (0, 255, 0), 2)

image = cv2.resize(image, None, fx=scale_x, fy=scale_y)
cv2.imshow("Detected Capsules", image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# %%
# binarize the image
binr = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)[1]

# define the kernel
kernel = np.ones((3, 3), np.uint8)

# invert the image
invert = cv2.bitwise_not(binr)

# use morph gradient
morph_gradient = cv2.morphologyEx(invert,
                                  cv2.MORPH_GRADIENT,
                                  kernel)

# print the output
plt.imshow(morph_gradient, cmap='gray')

# %%
