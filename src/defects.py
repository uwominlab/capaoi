#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Module containing functions to detect defects in the given capsule in an image.
"""

import cv2


MIN_BINARY_THRESH: int = 6


def detect_local_defects(capsule_raw, capsule_opened):
    # (原图掩膜操作>>均值滤波>>滤波图像原图进行差分>>二值化>>查找轮廓(根据轮廓长度进行筛选)
    draw_image = capsule_raw.copy()
    capsule_masked = cv2.bitwise_and(draw_image, draw_image, mask=capsule_opened)  # 对原始图像进行掩码运算
    # 截取胶囊中部视角
    window = [int(0.35 * capsule_masked.shape[1]), int(0.65 * capsule_masked.shape[1])]
    capsule_masked = capsule_masked[:, window[0]: window[1], :]

    img1 = capsule_masked
    img2 = capsule_masked
    # 中值滤波
    img1 = cv2.medianBlur(img1, 15)  # 均值滤波
    diff = cv2.absdiff(img1, img2)  # 图像差分

    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)  # 二值化
    minThres = 6
    _, thres = cv2.threshold(gray, minThres, 255, cv2.THRESH_BINARY)
    # 提取轮廓
    contours, hierarchy = cv2.findContours(thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # 缺陷轮廓排序，最大缺陷
    is_defect = False
    for i in range(0, len(contours)):
        length = cv2.arcLength(contours[i], True)
        # info = info + ">>>>局部缺陷长度: {}".format(length)
        # 通过轮廓长度筛选
        if 100 < length:
            is_defect = True
            cv2.drawContours(img2, contours[i], -1, (0, 0, 255), 2)
            # show_img("local_defects", img2)

    return is_defect


def detect_capsule_defects(
    capsule_images_raw: list[cv2.typing.MatLike],
    capsule_masks: list[cv2.typing.MatLike],
    capsule_centers: list[tuple[int, int]],
    capsule_sizes: list[tuple[int, int]],
    capsule_areas: list[float],
    capsule_similarities: list[float],
    normal_length_range: tuple[int, int] = (310, 320),
    normal_area_range: tuple[int, int] = (30500, 32000)
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

        # 1 >> Check if the capsule is too short or too long
        if not normal_length_range[0] <= length <= normal_length_range[1]:
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # 2 >> Check if the capsule has the proper area
        if not (normal_area_range[0] <= area <= normal_area_range[1]) and not is_abnormal:
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # 3 >> Check for contour similarity
        if similarity > 0.1 and not is_abnormal:  # Higher similarity indicates more deviation
            abnormal_capsule_centers.append(center)
            is_abnormal = True
            continue

        # 4 >> Defect detection
        capsule_opened = capsule_set_opened[ii]
        is_defect = detect_local_defects(capsule_raw, capsule_opened)
        if is_defect:
            is_abnormal = 1

        # 打印状态信息 info
        print(info)
        # cv2.putText(draw_image, 'Result flag: '+ str(result_flag), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
        # show_img("{}/{} capsules".format(ii, len(capsule_set_raw)), draw_image)

        if is_abnormal == 1:
            centers_abnormal_capsule.append(capsule_centers[ii])


        return abnormal_capsule_centers
