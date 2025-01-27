#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module contains helper Functions to transform an image.
"""


import cv2
import numpy as np


def cut_image_by_box(img: cv2.typing.MatLike, points: np.ndarray) -> cv2.typing.MatLike:
    """
    Extracts a region from the input image based on a given quadrilateral box (four points in clockwise order).

    Parameters:
        img (np.ndarray): The input image.
        points (np.ndarray): A 4x2 array of float32 representing the quadrilateral's corner points 
                             in clockwise order [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].

    Returns:
        np.ndarray: The extracted and transformed region of interest.

    Raises:
        ValueError: If the input points do not form a (4, 2) array.
    """
    points = np.float32(points)  # Ensure the points are in the correct dtype
    if points.shape != (4, 2):
        raise ValueError(
            "Points must be a 4x2 array representing four corners of a quadrilateral.")

    # Calculate the width and height of the transformed rectangle
    width = int(max(np.linalg.norm(
        points[0] - points[1]), np.linalg.norm(points[2] - points[3])))
    height = int(max(np.linalg.norm(
        points[1] - points[2]), np.linalg.norm(points[3] - points[0])))

    # Define the coordinates of the output rectangle's corners
    output_points = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)

    # Compute the perspective transformation matrix
    transformation_matrix = cv2.getPerspectiveTransform(points, output_points)

    # Perform the perspective warp
    transformed_image = cv2.warpPerspective(
        img, transformation_matrix, (width, height))

    return transformed_image


def get_img_opened(img_raw: cv2.typing.MatLike) -> cv2.typing.MatLike:
    """
    Applies a series of image processing operations to the input image.

    This function converts the input image to grayscale, applies a binary threshold,
    and then performs morphological closing followed by morphological opening.

    Args:
        img_raw (cv2.typing.MatLike): The raw input image.

    Returns:
        cv2.typing.MatLike: The processed image after applying the morphological operations.
    """
    img_gray: cv2.typing.MatLike = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    _, img_binary = cv2.threshold(img_gray, 125, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img_closed: cv2.typing.MatLike = cv2.morphologyEx(img_binary, cv2.MORPH_CLOSE, kernel)
    img_opened: cv2.typing.MatLike = cv2.morphologyEx(img_closed, cv2.MORPH_OPEN, kernel)
    return img_opened


def preprocess_image(image: cv2.typing.MatLike) -> cv2.typing.MatLike:
    """
    Function to preprocess an image by the following steps:
    1 - convert the image to grayscale
    2 - apply Gaussian Blur
    3 - enhance Contrast using CLAHE

    Args:
        image (np.ndarray): matrix-like 2 dimensional array of pixels

    Returns:
        mat: matrix-like 2 dim array of pixels
    """
    # Convert to Grayscale
    grayscale_image = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2GRAY)

    # Apply Gaussian Blur (or Median Filter)
    blurred_image = cv2.GaussianBlur(grayscale_image, (5, 5), 0)
    # filtered_image = cv2.medianBlur(grayscale_image, 5)  # median filtering

    # Enhance Contrast using CLAHE
    clahe: cv2.CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_image: cv2.typing.MatLike = clahe.apply(src=blurred_image)

    return enhanced_image
