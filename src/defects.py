#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Module containing functions to detect defects in the given capsule in an image.
"""

import cv2


MIN_BINARY_THRESH: int = 6


def detect_capsule_defects(
    capsule_images_raw: list[cv2.typing.MatLike],
    capsule_masks: list[cv2.typing.MatLike],
    capsule_centers: list[tuple[int, int]],
    capsule_sizes: list[tuple[int, int]],
    capsule_areas: list[float],
    capsule_similarities: list[float],
    normal_length_range: tuple[int, int] = (380, 400),
    normal_area_range: tuple[int, int] = (47000, 50000)
) -> list[tuple[int, int]]:
    """
    Detect defects in capsules based on multiple criteria.

    :param capsule_images_raw: List of cropped capsule images (raw images).
    :param capsule_masks: List of binary masks for the capsules.
    :param capsule_centers: List of capsule centers (e.g., for marking abnormalities).
    :param capsule_sizes: List of (length, width) for each capsule.
    :param capsule_areas: List of areas for each capsule.
    :param capsule_similarities: List of contour similarity scores for each capsule.
    :param normal_length_range: Tuple indicating the normal range of capsule lengths.
    :param normal_area_range: Tuple indicating the normal range of capsule areas.
    :return: List of centers of capsules flagged as abnormal.
    """
    abnormal_capsule_centers: list[tuple[int, int]] = []

    for (raw_image, mask, center, size, area, similarity) in zip(
            capsule_images_raw, capsule_masks, capsule_centers, capsule_sizes, capsule_areas, capsule_similarities):

        length, _ = size

        is_abnormal: bool = False

        # Check if the capsule is too short or too long
        if not normal_length_range[0] <= length <= normal_length_range[1]:
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # Check if the capsule has the proper area
        if not (normal_area_range[0] <= area <= normal_area_range[1]) and not is_abnormal:
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # Check for contour similarity
        if similarity > 0.1 and not is_abnormal:  # Higher similarity indicates more deviation
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # Defect detection
        masked_image = cv2.bitwise_and(raw_image, raw_image, mask=mask)
        # Focus on the central region of the capsule
        width_range = int(
            0.35 * masked_image.shape[1]), int(0.65 * masked_image.shape[1])
        central_region = masked_image[:, width_range[0]:width_range[1], :]

        # Perform median filtering and difference computation
        filtered = cv2.medianBlur(central_region, 15)
        difference = cv2.absdiff(filtered, central_region)

        # Convert to grayscale and threshold
        gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

        _, binary_diff = cv2.threshold(gray_diff, MIN_BINARY_THRESH, 255, cv2.THRESH_BINARY)
        # binary_diff = cv2.adaptiveThreshold(
        #     gray_diff, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Extract and filter contours
        contours, _ = cv2.findContours(
            binary_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            if cv2.arcLength(contour, True) > 50:  # Threshold contour length
                cv2.drawContours(central_region, [contour], -1, (0, 0, 255), 2)

        return abnormal_capsule_centers
