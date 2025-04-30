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

    # Step 2: Extract effective contours
    contours = [c for c in contours if 700 < c.shape[0] < 1100]

    # Step 3: Extracting the minimum bounding rectangle and its parameters for each contour
    rects, boxs, capsule_centers = [], [], []
    for contour in contours:
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

    # Step 4: Import the mask of the standard capsule
    mask_overall = cv2.findContours(
        mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_head = cv2.findContours(mask_binary[:int(
        0.20 * mask_binary.shape[0]), :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_tail = cv2.findContours(mask_binary[int(
        0.80 * mask_binary.shape[0]):, :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_overall, mask_head, mask_tail = (imutils.grab_contours(mask_overall),
                                          imutils.grab_contours(mask_head), imutils.grab_contours(mask_tail))
    if mask_overall and mask_head and mask_tail:
        mask_overall, mask_head, mask_tail = mask_overall[0], mask_head[0], mask_tail[0]
    else:
        raise ValueError("No contours found in the standard capsule mask.")

    # Step 5: Segment and analyze capsules
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
            target_raw = cv2.rotate(target_raw, cv2.ROTATE_90_COUNTERCLOCKWISE)
            target_opened = cv2.rotate(
                target_opened, cv2.ROTATE_90_COUNTERCLOCKWISE)

        capsule_set_raw.append(target_raw)
        capsule_set_opened.append(target_opened)

        # Analyze contours in the cropped denoised image
        length, width = max(rect[1]), min(rect[1])
        main_contour, similarity_overall = calculate_contours_similarity(
            target_opened, mask_overall)
        if main_contour:
            _, similarity_head = calculate_contours_similarity(
                target_opened[:int(0.20 * target_opened.shape[0]), :], mask_head)
            _, similarity_tail = calculate_contours_similarity(
                target_opened[int(0.80 * target_opened.shape[0]):, :], mask_tail)
            area = cv2.contourArea(main_contour)

            capsule_size.append(np.array([length, width]))
            capsule_area.append(area)
            capsule_similarity.append(
                [similarity_overall, similarity_head, similarity_tail])
        else:
            raise ValueError("No main_contour exist.")

    return (new_contours, capsule_set_raw, capsule_set_opened, rects,
            capsule_centers, capsule_size, capsule_area, capsule_similarity)


def calculate_contours_similarity(target_opened, contour_mask):
    """
    :param target_opened: binary capsule image
    :param contour_mask: Binary mask of the standard capsule contour.
    :return:
        - main_contour: Contours for cropped capsules.
        - similarity: Similarity between target_opened and contour_mask.
    """
    # Extract capsule contour
    contours = cv2.findContours(
        target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本
    # Take the largest contour as the main contour
    main_contour = max(contours, key=cv2.contourArea)  # 提取主轮廓
    similarity = cv2.matchShapes(
        contour_mask, main_contour, cv2.CONTOURS_MATCH_I1, 0.0)
    return main_contour, similarity
