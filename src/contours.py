#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for contour detection and extraction.
"""


import cv2
import numpy as np
import imutils

from utils.transform import cut_image_by_box


def find_contours_img(
    img_raw: cv2.typing.MatLike,
    img_opened: cv2.typing.MatLike,
    mask_binary: cv2.typing.MatLike
) -> tuple[list, list, list, list, list, list, list, list]:
    """
    Process images to detect capsule contours and extract relevant information.

    :param img_raw: Original image.
    :param img_opened: Denoised binary image.
    :param mask_binary: Binary mask of the standard capsule contour.
    :return: Tuple containing:
        - new_contours: Refined contours for cropped capsules.
        - capsule_set_raw: Cropped raw images of capsules.
        - capsule_set_opened: Cropped denoised images of capsules.
        - rects: Minimum enclosing rectangles for capsules.
        - capsule_centers: Pixel centers of the capsules.
        - capsule_size: Dimensions of the capsules (length, width).
        - capsule_area: Areas of the capsule contours.
        - capsule_similarity: Similarity scores to the standard mask.
    """
    # Step 1: Detect contours in the denoised image
    contours = cv2.findContours(
        img_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    # Step 2: Filter valid contours based on size threshold
    rects, boxs, capsule_centers = [], [], []
    for contour in contours:
        if 700 < len(contour) < 1100:  # Adjust thresholds as needed
            rect = cv2.minAreaRect(contour)
            rects.append(rect)
            capsule_centers.append(rect[0])
            box = np.int64(cv2.boxPoints(rect))
            boxs.append(box)

    # Visualization (optional)
    draw_img = img_raw.copy()
    draw_img = cv2.drawContours(draw_img, boxs, -1, (0, 0, 255), 2)
    for center in capsule_centers:
        cv2.circle(draw_img, (int(center[0]), int(
            center[1])), 10, (0, 255, 0), -1)
    cv2.namedWindow(winname="Detected Capsules", flags=cv2.WINDOW_NORMAL)
    cv2.imshow(winname="Detected Capsules", mat=draw_img)

    # Step 3: Process the standard capsule mask
    contours_mask = cv2.findContours(
        mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_mask = imutils.grab_contours(contours_mask)
    if contours_mask:
        contours_mask = contours_mask[0]
    else:
        raise ValueError("No contours found in the standard capsule mask.")

    # Step 4: Segment and analyze capsules
    new_contours, capsule_set_raw, capsule_set_opened = [], [], []
    capsule_size, capsule_area, capsule_similarity = [], [], []
    for rect in rects:
        # Expand the rectangle slightly for cropping
        new_rect_size = (1.1 * rect[1][0], 1.2 * rect[1][1])
        expanded_rect = (rect[0], new_rect_size, rect[2])
        cut_box = np.int64(cv2.boxPoints(expanded_rect))

        # Crop images
        target_raw = cut_image_by_box(img_raw, cut_box)
        target_opened = cut_image_by_box(img_opened, cut_box)

        # Ensure horizontal alignment
        if target_raw.shape[0] > target_raw.shape[1]:
            target_raw = cv2.rotate(target_raw, cv2.ROTATE_90_CLOCKWISE)
            target_opened = cv2.rotate(target_opened, cv2.ROTATE_90_CLOCKWISE)

        capsule_set_raw.append(target_raw)
        capsule_set_opened.append(target_opened)

        # Analyze contours in the cropped denoised image
        inner_contours = cv2.findContours(
            target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        inner_contours = imutils.grab_contours(inner_contours)
        if inner_contours:
            # Take the largest contour
            main_contour = max(inner_contours, key=cv2.contourArea)
            new_contours.append(main_contour)

            # Capsule parameters
            length, width = max(rect[1]), min(rect[1])
            area = cv2.contourArea(main_contour)
            similarity = cv2.matchShapes(
                contours_mask, main_contour, cv2.CONTOURS_MATCH_I1, 0)

            capsule_size.append((length, width))
            capsule_area.append(area)
            capsule_similarity.append(similarity)

    return (new_contours, capsule_set_raw, capsule_set_opened, rects,
            capsule_centers, capsule_size, capsule_area, capsule_similarity)
