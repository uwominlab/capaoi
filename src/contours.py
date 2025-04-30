#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for contour detection and extraction.
"""

import cv2
import numpy as np
from imutils import grab_contours

from utils.transform import cut_image_by_box


CONTOURS_DETECTION_DEBUG: bool = True


# pylint: disable=too-many-locals
def find_contours_img(
    img_raw: cv2.typing.MatLike,
    img_opened: cv2.typing.MatLike,
    mask_binary: cv2.typing.MatLike
) -> tuple[list, list, list, list, list, list]:
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

    >>> import numpy as np
    >>> img_raw = np.zeros((100, 100), dtype=np.uint8)
    >>> img_opened = np.zeros((100, 100), dtype=np.uint8)
    >>> mask_binary = np.zeros((100, 100), dtype=np.uint8)
    >>> _ = cv2.rectangle(img_opened, (30, 30), (70, 70), 255, -1)
    >>> _ = cv2.rectangle(mask_binary, (30, 30), (70, 70), 255, -1)
    >>> result = find_contours_img(img_raw, img_opened, mask_binary)
    >>> len(result[0]) == len(result[1]) == len(result[2])  # Number of detected capsules
    True
    >>> len(result[3]) == len(result[4]) == len(result[5])  # Size, area, similarity data
    True
    """
    # Step 1: Detect contours in the denoised image
    contours = cv2.findContours(img_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = grab_contours(contours)

    # Step 2: Filter valid contours based on size threshold
    # Sort the contours of the capsules in the list （x, y, w, h
    # Retreive the rectangular bounding box, x coordinates decreasing order (from right to left)
    # and y coordinates increasing order (from bottom to top)
    contours = [c for c in contours if 400 < len(c) < 1500]
    contours = sorted(contours, key=lambda c: (-cv2.boundingRect(c)[0], cv2.boundingRect(c)[1]))

    # Step 3: Extracting the minimum bounding rectangle and its parameters for each contour
    rects, boxs, capsule_centers = [], [], []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        capsule_centers.append(rect[0])
        rects.append(rect)
        box = np.int64(cv2.boxPoints(rect))
        boxs.append(box)

    # Visualization (optional)
    if CONTOURS_DETECTION_DEBUG:
        draw_img = img_raw.copy()
        draw_img = cv2.drawContours(draw_img, boxs, -1, (0, 0, 255), 2)
        for index, center in enumerate(capsule_centers):
            cv2.circle(draw_img, (int(center[0]), int(center[1])),
                       10, (0, 255, 0), -1)
            cv2.putText(draw_img, str(index + 1),
                (int(center[0]), int(center[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
        cv2.imwrite("Detected_Capsules.png", draw_img)

    # Step 4: Import the mask of the standard capsule
    mask_overall = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_head = cv2.findContours(mask_binary[:int(0.20 * mask_binary.shape[0]), :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_tail = cv2.findContours(mask_binary[int(0.80 * mask_binary.shape[0]):, :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_overall, mask_head, mask_tail = (grab_contours(mask_overall),
                                          grab_contours(mask_head), grab_contours(mask_tail))
    if mask_overall and mask_head and mask_tail:
        mask_overall, mask_head, mask_tail = mask_overall[0], mask_head[0], mask_tail[0]
    else:
        raise ValueError("No contours found in the standard capsule mask.")

    # Step 5: Segment and analyze capsules
    capsule_set_raw: list[cv2.typing.MatLike] = []
    capsule_set_opened: list[cv2.typing.MatLike] = []
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
            target_raw = cv2.rotate(target_raw, cv2.ROTATE_90_COUNTERCLOCKWISE)
            target_opened = cv2.rotate(target_opened, cv2.ROTATE_90_COUNTERCLOCKWISE)

        capsule_set_raw.append(target_raw)
        capsule_set_opened.append(target_opened)

        # Analyze contours in the cropped denoised image
        length, width = max(rect[1]), min(rect[1])
        main_contour, similarity_overall = calculate_contours_similarity(
            target_opened, mask_overall)
        if main_contour is not None:
            _, similarity_head = calculate_contours_similarity(
                target_opened[:int(0.20 * target_opened.shape[0]), :], mask_head)
            _, similarity_tail = calculate_contours_similarity(
                target_opened[int(0.80 * target_opened.shape[0]):, :], mask_tail)
            area: float = cv2.contourArea(main_contour)

            capsule_size.append(np.array([length, width]))
            capsule_area.append(area)
            capsule_similarity.append([similarity_overall, similarity_head, similarity_tail])
        else:
            raise ValueError("No main_contour exist.")

    return (
        capsule_set_raw, capsule_set_opened,
        capsule_centers, capsule_size, capsule_area, capsule_similarity
    )


def calculate_contours_similarity(
    target_opened: cv2.typing.MatLike, contour_mask: cv2.typing.MatLike
) -> tuple[cv2.typing.MatLike, float]:
    """
    :param target_opened: Binary capsule image.
    :param contour_mask: Binary mask of the standard capsule contour.
    :return:
        - main_contour: Contours for cropped capsules.
        - similarity: Similarity between target_opened and contour_mask.
    """
    # Extract capsule contour
    contours = cv2.findContours(target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = grab_contours(contours)
    # Take the largest contour as the main contour
    if contours:
        main_contour: cv2.typing.MatLike = max(contours, key=cv2.contourArea)
        similarity: float = cv2.matchShapes(
            contour1=contour_mask,
            contour2=main_contour,
            method=cv2.CONTOURS_MATCH_I1,
            parameter=0.0)
        return main_contour, similarity


if __name__ == "__main__":
    import doctest
    doctest.testmod()
