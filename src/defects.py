#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Module containing functions to detect defects in the given capsule in an image.
"""

import logging
# pylint: disable=no-name-in-module
from cv2 import absdiff, arcLength, bitwise_and, cvtColor, findContours, medianBlur, threshold
from cv2 import COLOR_BGR2GRAY, CHAIN_APPROX_NONE, RETR_EXTERNAL, THRESH_BINARY
from cv2.typing import MatLike

from PyQt6.QtCore import QSettings


MIN_BINARY_THRESH: int = 6
MAX_LENGTH: int = 0

settings: QSettings = QSettings("MinLab", "CapAOI")
DEFECTS_DETECTION_DEBUG: bool = settings.value(
    "defect/debug", type=bool, defaultValue=False)
logging.basicConfig(
    level=logging.DEBUG if DEFECTS_DETECTION_DEBUG else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def detect_defects(
    raw_image: MatLike,
    mask: MatLike,
    local_defect_length: int
) -> tuple[bool, float]:
    """
    Detect defects in the given capsule image based on the mask.

    Args:
        raw_image (MatLike): Original capsule image.
        mask (MatLike): Binary mask for the capsule.
        local_defect_length (int): Length threshold for detecting local defects.

    Returns:
        tuple[bool, float]: True if a defect is detected, False otherwise.
        A float representing the maximum length of the detected defect.
    """
    masked_image = bitwise_and(raw_image, raw_image, mask=mask)
    # Focus on the central region of the capsule
    width_range: tuple[int, int] = (
        int(0.40 * masked_image.shape[1]), int(0.60 * masked_image.shape[1]))
    central_region = masked_image[:, width_range[0]:width_range[1], :]

    # Perform median filtering and difference computation
    filtered = medianBlur(central_region, 15)
    difference = absdiff(filtered, central_region)

    # Convert to grayscale and threshold
    gray_diff = cvtColor(difference, COLOR_BGR2GRAY)

    _, binary_diff = threshold(
        gray_diff, MIN_BINARY_THRESH, 255, THRESH_BINARY)

    # Extract and filter contours
    contours, _ = findContours(binary_diff, RETR_EXTERNAL, CHAIN_APPROX_NONE)

    partial_defect: bool = False
    max_length: float = 0.0
    for contour in contours:
        length: float = arcLength(contour, closed=True)
        if local_defect_length <= length and max_length <= length:
            max_length = length
            partial_defect = True

    return partial_defect, max_length


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-locals
def detect_capsule_defects(
    capsule_images_raw: list[MatLike],
    capsule_masks: list[MatLike],
    capsule_centers: list[tuple[int, int]],
    capsule_sizes: list[tuple[int, int]],
    capsule_areas: list[float],
    capsule_similarities: list[list[float]],
    normal_length_range: tuple[int, int],
    normal_width_range: tuple[int, int] = (100, 150),
    normal_area_range: tuple[int, int] = (30500, 35000),
    similarity_threshold_overall: float = 0.1,
    similarity_threshold_head: float = 0.3,
    local_defect_length: int = 75
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
    :param similarity_threshold_overall: Threshold for contour similarity.
    :param similarity_threshold_head: 头部相似度阈值（低于阈值为正常）
    :param local_defect_length: Length threshold for detecting local defects.
    :return: List of centers of capsules flagged as abnormal.
    """
    # list of abnormal capsule centers, each indicated in the form of a point (x, y)
    abnormal_capsule_centers: list[tuple[int, int]] = []

    for index, (raw_image, mask, center, size, area, similarities) in enumerate(
        zip(
            capsule_images_raw, capsule_masks, capsule_centers,
            capsule_sizes, capsule_areas, capsule_similarities
        )
    ):

        length, width = size

        # Step 0 >> Check if the capsule is already marked as abnormal
        if center in abnormal_capsule_centers:
            continue

        # Step 1 >> Check if the capsule is too short or too long
        if not normal_length_range[0] <= length <= normal_length_range[1] and \
                center not in abnormal_capsule_centers:
            abnormal_capsule_centers.append(center)
            if not DEFECTS_DETECTION_DEBUG:
                continue

        # Step 2 >> Check if the capsule has the proper area
        if not normal_area_range[0] <= area <= normal_area_range[1] and \
                center not in abnormal_capsule_centers:
            abnormal_capsule_centers.append(center)
            if not DEFECTS_DETECTION_DEBUG:
                continue

        # Step 3 >> Check for contour similarity
        # Higher similarity indicates more deviation from the expected shape
        similarity_overall, similarity_head, similarity_tail = \
            similarities[0], similarities[1], similarities[2]

        is_abnormal_similarity: bool =\
            similarity_threshold_overall <= similarity_overall \
            or similarity_threshold_head < similarity_head or similarity_threshold_head < similarity_tail
        if is_abnormal_similarity and center not in abnormal_capsule_centers:
            abnormal_capsule_centers.append(center)
            if not DEFECTS_DETECTION_DEBUG:
                continue

        # Step 4 >> Defect detection
        partial_defect, max_length = detect_defects(raw_image, mask, local_defect_length)
        if partial_defect and center not in abnormal_capsule_centers:
            abnormal_capsule_centers.append(center)
            if not DEFECTS_DETECTION_DEBUG:
                continue

        if DEFECTS_DETECTION_DEBUG:
            info: str = \
                f"{index + 1} of {len(capsule_images_raw)} capsules:\n" + \
                f"Length: {length:.2f} (Normal Range: {normal_length_range}), Width: {width:.2f}\n" \
                f"Length Normal: {normal_length_range[0] <= length <= normal_length_range[1]}\n" \
                f"Area: {area:.2f} (Normal Range: {normal_area_range})\n" \
                f"Area Normal: {normal_area_range[0] <= area <= normal_area_range[1]}\n" \
                f"Contour Similarity: {similarity_overall:.4f}, {similarity_head:.4f}, {similarity_tail:.4f} (Lower is better)\n" \
                f"Similarities: {similarity_threshold_overall <= similarity_overall}, {similarity_threshold_head < similarity_head}, {similarity_threshold_head < similarity_tail}\n" \
                f"Local Defect Length: {max_length}\n" \
                f"Partial Defect Detected: {partial_defect}\n"
            logging.debug(info)

    return abnormal_capsule_centers
