#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Module containing functions to detect defects in the given capsule in an image.
"""

import cv2


MIN_BINARY_THRESH: int = 6
max_length: int = 0

def detect_defects(raw_image: cv2.typing.MatLike, mask: cv2.typing.MatLike, length, width, local_defect_length) -> bool:
    """
    Detect defects in the given capsule image based on the mask.

    Args:
        raw_image (cv2.typing.MatLike): Original capsule image.
        mask (cv2.typing.MatLike): Binary mask for the capsule.
        length (): capsule length.
        width (): capsule width.
        local_defect_length ():  defect length threshold (Below the threshold is considered normal)

    Returns:
        bool: True if a defect is detected, False otherwise.
    """
    masked_image = cv2.bitwise_and(raw_image, raw_image, mask=mask)
    # Focus on the central region of the capsule
    width_range_1 = [int(0.5 * draw_image.shape[0] - 0.15 * length), int(0.5 * draw_image.shape[0] + 0.15 * length)]  # Cut up and down
    width_range_2 = [int(0.5 * draw_image.shape[1] - 0.45 * width), int(0.5 * draw_image.shape[1] + 0.45 * width)]  # Cut left and right
    central_region = masked_image[width_range_1[0]:width_range_1[1], width_range_2[0]:width_range_2[1], :]

    # Perform median filtering and difference computation
    filtered = cv2.medianBlur(central_region, 15)
    difference = cv2.absdiff(filtered, central_region)

    # Convert to grayscale and threshold
    gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    _, binary_diff = cv2.threshold(
        gray_diff, MIN_BINARY_THRESH, 255, cv2.THRESH_BINARY)

    # Extract and filter contours
    contours, _ = cv2.findContours(
        binary_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    is_defect = False
    for contour in contours:
        if local_defect_length < cv2.arcLength(contour, True):  # Threshold contour length
            is_defect = True
            # cv2.drawContours(central_region, [contour], -1, (0, 0, 255), 2)  # only used for debug
    # if is_defect:
    #     show_img("local_defects of {}-th capsule".format(capsule_id), central_region)
    return is_defect


def detect_local_defects(capsule_raw, capsule_opened, length, width, local_defect_length, capsule_id):
    # (原图掩膜操作>>均值滤波>>滤波图像原图进行差分>>二值化>>查找轮廓(根据轮廓长度进行筛选)
    draw_image = capsule_raw.copy()
    capsule_masked = cv2.bitwise_and(draw_image, draw_image, mask=capsule_opened)  # 对原始图像进行掩码运算
    show_img("capsule_masked", capsule_masked)
    # 截取胶囊中部视角（上下帽体结合处）
    window1 = [int(0.5 * draw_image.shape[0] - 0.15 * length), int(0.5 * draw_image.shape[0] + 0.15 * length)]  # 上下截取
    window2 = [int(0.5 * draw_image.shape[1] - 0.45 * width), int(0.5 * draw_image.shape[1] + 0.45 * width)]  # 左右截取
    capsule_masked = draw_image[window1[0]: window1[1], window2[0]: window2[1], :]
    show_img("capsule_masked", capsule_masked)

    img1 = capsule_masked
    img2 = capsule_masked
    img1 = cv2.medianBlur(img1, 15)  # 均值滤波
    diff = cv2.absdiff(img1, img2)  # 图像差分
    show_img("diff", diff)  # 差分结果图
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)  # 二值化
    minThres = 6  # 控制对缺陷的敏感度
    _, thres = cv2.threshold(gray, minThres, 255, cv2.THRESH_BINARY)
    show_img("thres", thres)  # 差分结果图
    contours, _ = cv2.findContours(thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # sorted_contours = sorted(contours, key=lambda c: cv2.arcLength(c, True), reverse=True)

    # 缺陷轮廓长度检测，最大缺陷
    max_length, is_defect = 0, False
    for ii in range(0, len(contours)):
        length = cv2.arcLength(contours[ii], True)
        # 轮廓长度判断
        if local_defect_length <= length and max_length <= length:
            max_length = length
            is_defect = True
            cv2.drawContours(img2, contours[ii], -1, (0, 0, 255), 2)
    if is_defect:
        show_img("local_defects of {}-th capsule".format(capsule_id), img2)
    return is_defect, max_length


def detect_capsule_defects(
    capsule_images_raw: list[cv2.typing.MatLike],
    capsule_masks: list[cv2.typing.MatLike],
    capsule_centers: list[tuple[int, int]],
    capsule_sizes: list[tuple[int, int]],
    capsule_areas: list[float],
    capsule_similarities: list[float],
    normal_length_range: tuple[int, int] = (310, 330),
    normal_area_range: tuple[int, int] = (30500, 34000),
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
    :param similarity_threshold_overall: float indicating the threshold of the overall similarity.
    :param similarity_threshold_head: float indicating the threshold of the head/tail similarity.
    :param local_defect_length: int indicating the threshold of local defect length.
    :return: List of centers of capsules flagged as abnormal.
    """
    abnormal_capsule_centers: list[tuple[int, int]] = []

    for (raw_image, mask, center, size, area, similarity) in zip(
            capsule_images_raw, capsule_masks, capsule_centers, capsule_sizes, capsule_areas, capsule_similarities):

        length, _ = size

        # Step 1 >> Check if the capsule is too short or too long
        if not normal_length_range[0] <= length <= normal_length_range[1]:
            abnormal_capsule_centers.append(center)
            continue

        # Step 2 >> Check if the capsule has the proper area
        if not (normal_area_range[0] <= area <= normal_area_range[1]):
            abnormal_capsule_centers.append(center)
            continue

        # Step 3 >> Check for contour similarity
        if similarity > 0.04:  # Higher similarity indicates more deviation
            abnormal_capsule_centers.append(center)
            continue

        # Step 4 >> Defect detection
        is_defect = detect_defects(raw_image, mask)
        if is_defect:
            abnormal_capsule_centers.append(center)

        return abnormal_capsule_centers
