#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module contains helper Functions to transform an image.
"""


import cv2
import numpy as np


def generate_background_mask(image_rgb: np.ndarray, bgc_ranges: dict) -> np.ndarray:
    """
    Generates a combined background mask for the specified RGB ranges.

    Parameters:
        image_rgb (np.ndarray): RGB image.
        bgc_ranges (dict): Dictionary of color names to (lower, upper) RGB range tuples.

    Returns:
        np.ndarray: Combined binary mask for all specified background ranges.
    """
    combined_mask: np.ndarray = np.zeros(image_rgb.shape[:2], dtype=np.uint8)
    for lower, upper in bgc_ranges.values():
        lower_np = np.array(lower, dtype=np.uint8)
        upper_np = np.array(upper, dtype=np.uint8)
        mask = cv2.inRange(image_rgb, lower_np, upper_np)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    return combined_mask


def remove_background(img_bgr: np.ndarray, bgc_ranges: dict) -> np.ndarray:
    """
    Removes background colors from an image using specified RGB ranges.

    Parameters:
        img_bgr (np.ndarray): Original BGR image.
        bgc_ranges (dict): Dictionary mapping color names to (lower, upper) RGB tuples.

    Returns:
        np.ndarray: BGR image with background pixels set to black.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    background_mask = generate_background_mask(img_rgb, bgc_ranges)
    foreground_mask = cv2.bitwise_not(background_mask)
    img_bgr_no_bg = cv2.bitwise_and(img_bgr, img_bgr, mask=foreground_mask)
    return img_bgr_no_bg


def cut_image_by_box(img: cv2.typing.MatLike, points: np.ndarray) -> cv2.typing.MatLike:
    """
    Extracts a region from the input image based on a given quadrilateral box
    (four points in clockwise order).

    Parameters:
        img (np.ndarray): The input image.
        points (np.ndarray): A 4x2 array of float32 representing the quadrilateral's corner points
                             in clockwise order [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].

    Returns:
        np.ndarray: The extracted and transformed region of interest.

    Raises:
        ValueError: If the input points do not form a (4, 2) array.
    """
    points = points.astype(np.float32)  # Ensure correct dtype
    if points.shape != (4, 2):
        raise ValueError(
            "Points must be a 4x2 array representing four corners of a quadrilateral.")

    # Calculate the width and height of the transformed rectangle
    width = int(max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])))  # type: ignore
    height = int(max(np.linalg.norm(points[1] - points[2]), np.linalg.norm(points[3] - points[0])))  # type: ignore

    # Define the coordinates of the output rectangle's corners
    output_points = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]],
        dtype=np.float32)

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
    # Step 1: Grayscale image
    img_gray: cv2.typing.MatLike = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    # Step2: Median filtering: removing salt and pepper noise while preserving edges
    img_gray = cv2.medianBlur(img_gray, 15)
    # Step 3: Binary image to highlight capsules
    img_binary = cv2.inRange(img_gray, 1, 255)  # type: ignore

    # Step 4: Morphological open operation: first corrode and dilate expand, remove small noise points
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    # img_binary: cv2.typing.MatLike = cv2.morphologyEx(img_binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    img_opened: cv2.typing.MatLike = cv2.morphologyEx(
        img_binary, cv2.MORPH_OPEN, kernel, iterations=1)
    return img_opened

def remove_zero_rows(binary_img: cv2.typing.MatLike) -> cv2.typing.MatLike:
    """
    Removes rows that are entirely zero from the binary image.
    This is useful for cleaning up the image after morphological operations.

    Args:
        binary_img (cv2.typing.MatLike): The binary image from which to remove zero rows.

    Raises:
        ValueError: If the input binary image is a zero matrix.

    Returns:
        cv2.typing.MatLike: The binary image with zero rows removed.
    """
    non_zero_rows = np.any(binary_img != 0, axis=1)
    row_indices = np.where(non_zero_rows)[0]
    if len(row_indices) > 0:
        top, bottom = row_indices[0], row_indices[-1]
        binary_img = binary_img[top:bottom + 1, :]
    else:
        raise ValueError("The input binary image is a zero matrix.")
    return binary_img
