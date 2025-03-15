import os
from src.params import ROOT_DIR

import cv2
import numpy as np
import imutils
import time
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams['figure.dpi'] = 300   # 图形的DPI

os.path.join(ROOT_DIR)


def show_img(img_name, img):
    if len(img_raw.shape)==3:
        # plt.imshow(img, 'gray')
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img)
    else:
        plt.imshow(img, 'gray')
    plt.axis('off')
    plt.title(img_name)
    plt.show()


def CutImgeByBox(img, points):
    """
    根据任意内接矩形，四点（顺时针）box[[x1,y2],[x2,y2],[x3,y3],[x4,y4]]，从输入图像中，截取图像
    """
    points = np.float32(points)
    if points.shape == (4, 2):
        # 计算图像的宽度和高度：
        width = max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3]))
        height = max(np.linalg.norm(points[1] - points[2]), np.linalg.norm(points[3] - points[0]))
        # 定义输出图像的四个角点坐标：
        output_points = np.array([(0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1)], dtype=np.float32)
        # 计算透视变换矩阵：
        matrix = cv2.getPerspectiveTransform(points, output_points)
        # 进行透视变换：
        target = cv2.warpPerspective(img, matrix, (int(width), int(height)))
    else:
        raise ValueError("box shape is wrong, must be (4,2)")
    return target


def img_preprocessing(img_raw):
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)                     # 图像灰度化
    # show_img("img_gray", img_gray)
    # img_blurred = cv2.GaussianBlur(img_gray, (3, 3), 0)                      # 高斯模糊抑制背景噪声（调整卷积核大小）
    # show_img("img_blurred", img_blurred)
    _, img_binary = cv2.threshold(img_gray, 125, 255, cv2.THRESH_BINARY)  # 图像二值化， 阈值=165（阈值影响开闭运算效果）
    # show_img("img_binary", img_binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))          # 定义矩形结构元素
    img_closed = cv2.morphologyEx(img_binary, cv2.MORPH_CLOSE, kernel)  # 闭运算（链接块）
    # show_img("img_closed", img_closed)
    img_opened = cv2.morphologyEx(img_closed, cv2.MORPH_OPEN, kernel)   # 开运算（去噪点）
    # show_img("filtered_binary_img", img_opened)

    return img_raw, img_opened


def find_contours_img(img_raw, img_opened, mask_binary):
    """
    :param img_raw: 原始图像
    :param img_opened:  去噪后的图像
    :return:
       new_contours         裁剪后胶囊的新轮廓(裁剪后，像素变少，原来求的轮廓不在适用)
       capsule_set_raw      图像裁剪后，胶囊的原始图像
       capsule_set_opened   图像裁剪后，胶囊的去噪图像
       rects:               胶囊的最小外接矩形 info: rect_center, rect_scale, rotation_angle
       boxs:                胶囊的最小外接矩形的顶点
       centers:             胶囊在原始图像中的像素中心
    """

    contours = cv2.findContours(img_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 输入图像（二值图像，黑色作为背景，白色作为目标），轮廓检索方式，
    contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本

    # 轮廓检验：如果某物体轮廓点数量位于阈值区间，则认为是 胶囊
    rects = []
    boxs = []
    capsule_centers = []
    for contour in contours:
        if 700 < contour.shape[0] and contour.shape[0] < 1100:
        # if 400 < contour.shape[0] and contour.shape[0] < 1500:
            # 求有效轮廓的最小外接矩形, 返回 center(x,y), (width, height), angle of rotation
            rect = cv2.minAreaRect(contour)
            capsule_centers.append(rect[0])
            rects.append(rect)
            rect_center, rect_scale, rotation_angle = rect[0], rect[1], rect[2]
            box = np.int64(cv2.boxPoints(rect))  # 通过函数cv2.boxPoints获得绘制这个矩形需要矩形的4个角点
            boxs.append(box)
            # cv2.circle(draw_img, (rect[0][0], y[0][1]), r, (0, 255, 0), 4)
    # draw_img = cv2.drawContours(img_raw.copy(), boxs, -1, (0, 0, 255), 2)
    # for center in capsule_centers:
    #     cv2.circle(draw_img, (int(center[0]), int(center[1])), 10, (0, 0, 255), 10)
    # show_img("contour_defection_results", draw_img)

    # 导入标准胶囊的轮廓 mask
    contours_mask = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours_mask = imutils.grab_contours(contours_mask)
    contours_mask = contours_mask[0]

    new_rects = []
    new_contours = []
    capsule_set_raw = []
    capsule_set_opened = []
    capsule_size = []          # 胶囊轮廓尺寸(胶囊的最小外接矩形长宽)
    capsule_area = []          # 胶囊轮廓面积
    capsule_similarity = []    # 胶囊与标准胶囊的轮廓相似度

    # 图像分割
    for ii in range(len(rects)):
        rect = rects[ii]
        # 最小外接矩形以中心，把 1.1 倍真实长度, 1.2 倍真实宽度 来分割图像
        nwe_rect_size = [1.1*rect[1][0], 1.2*rect[1][1]]
        nwe_rect = [rect[0], nwe_rect_size, rect[2]]
        new_rects.append(nwe_rect)
        cut_box = np.int64(cv2.boxPoints(nwe_rect))  # 通过函数cv2.boxPoints获得绘制这个矩形需要矩形的4个角点

        # 裁剪图像
        target_raw = CutImgeByBox(img_raw, cut_box)
        target_opened = CutImgeByBox(img_opened, cut_box)

        # 如果横向排布，变成纵向
        if target_raw.shape[0] < target_raw.shape[1]:
            target_raw = cv2.rotate(target_raw, cv2.ROTATE_90_COUNTERCLOCKWISE)
            target_opened = cv2.rotate(target_opened, cv2.ROTATE_90_COUNTERCLOCKWISE)
        capsule_set_raw.append(target_raw)
        capsule_set_opened.append(target_opened)

        # 胶囊参数计算：长度length  宽度width  面积area  轮廓相似度similarity
        contours = cv2.findContours(target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 输入图像（二值图像，黑色作为背景，白色作为目标），轮廓检索方式，
        contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本
        contours = sorted(contours, key=len, reverse=True)
        new_contours.append(contours[0])

        length, width = np.max(rects[ii][1]), np.min(rects[ii][1])
        area = cv2.contourArea(contours[0])
        # 整体轮廓相似度
        similarity_overall = cv2.matchShapes(contours_mask, contours[0], 1, 0.0)
        # 胶囊头部、尾部相似度
        similarity_head =  cv2.matchShapes(contours_mask[:int(0.20*contours_mask.shape[0]), :, :],
                                         contours[0][:int(0.20*contours[0].shape[0]), :, :] , 1, 0.0)
        similarity_tail =  cv2.matchShapes(contours_mask[int(0.80*contours_mask.shape[0]):, :, :],
                                         contours[0][int(0.80*contours[0].shape[0]):, :, :] , 1, 0.0)

        capsule_size.append(np.array([length, width]))
        capsule_area.append(area)
        capsule_similarity.append([similarity_overall, similarity_head, similarity_tail])
        target_raw_copy = target_raw.copy()
        cv2.drawContours(target_raw_copy, contours, -1, (0, 255, 0), 3)
        # show_img("{}/{} capsules >> L: {:.2f} W: {:.2f} Area: {}".format(ii+1, len(rects), length, width, area), target_raw_copy)
        # show_img("{}/{} capsules: ".format(ii+1, len(rects)), target_opened)

    return new_contours, capsule_set_raw, capsule_set_opened, boxs, capsule_centers, capsule_size, capsule_area, capsule_similarity



def detect_local_defects(capsule_raw, capsule_opened, local_defect_length, capsule_id):
    # (原图掩膜操作>>均值滤波>>滤波图像原图进行差分>>二值化>>查找轮廓(根据轮廓长度进行筛选)
    draw_image = capsule_raw.copy()
    capsule_masked = cv2.bitwise_and(draw_image, draw_image, mask=capsule_opened)  # 对原始图像进行掩码运算
    # show_img("capsule_masked", capsule_masked)
    # 截取胶囊中部视角
    window = [int(0.40 * capsule_masked.shape[0]), int(0.60 * capsule_masked.shape[0])]
    capsule_masked = capsule_masked[window[0]: window[1], :, :]

    img1 = capsule_masked
    img2 = capsule_masked
    # 中值滤波
    img1 = cv2.medianBlur(img1, 15)  # 均值滤波
    diff = cv2.absdiff(img1, img2)  # 图像差分
    # show_img("diff", diff)  # 差分结果图

    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)  # 二值化
    minThres = 6
    _, thres = cv2.threshold(gray, minThres, 255, cv2.THRESH_BINARY)
    # show_img("thres", thres)  # 差分结果图
    # 提取轮廓
    contours, hierarchy = cv2.findContours(thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # 缺陷轮廓排序，最大缺陷
    is_defect = False
    # contours = sorted(contours, key=len, reverse=True)
    max_length = 0
    for i in range(0, len(contours)):
        length = cv2.arcLength(contours[i], True)
        # info = info + ">>>>局部缺陷长度: {}".format(length)
        # 通过轮廓长度筛选
        if local_defect_length <= length and max_length < length:
            max_length = length
            is_defect = True
            cv2.drawContours(img2, contours[i], -1, (0, 0, 255), 2)
    # if is_defect:
    #     show_img("local_defects of {}-th capsule".format(capsule_id), img2)

    return is_defect, max_length



def capsule_defect_detection(capsule_set_raw, capsule_set_opened,  capsule_centers, capsule_size, capsule_area, capsule_similarity,
                             nor_len_range=[310, 330], nor_area_range=[30500, 35000],
                             similarity_threshold=0.05, local_defect_length=75):
    """
    :param capsule_set_raw:    胶囊的裁剪图 原图
    :param capsule_set_opened: 胶囊的裁剪 二值图
    :param capsule_centers:    胶囊的在capsule_set_raw中的中心坐标
    :param capsule_size:       胶囊的尺寸
    :param capsule_area:       胶囊面积
    :param capsule_similarity: 胶囊的相似度
    :param nor_len_range:      正常长度范围（范围内为正常）
    :param nor_area_range:     正常面积范围（范围内为正常）
    :param similarity_threshold: 相似度阈值（低于阈值为正常）
    :param nor_area_range:     正常面积范围（低于阈值为正常）
    :return:
        abnormal_capsule_centers:  异常胶囊中心坐标（像素点坐标）
        all_capsule_centers:       所有胶囊中心坐标（像素点坐标）
    """

    abnormal_capsule_centers = []
    all_capsule_centers = []
    L, W, A, S = [], [], [], []  # 存储所有胶囊的长、宽、面积、轮廓相似度

    for ii in range(0, len(capsule_set_raw)):
        capsule_raw = capsule_set_raw[ii]
        info = "{} of {} capsules: \n".format(ii + 1, len(capsule_set_raw))
        is_abnormal = False

        # 检测项目1：长度检测 >> 对比 待测胶囊的最小外接矩形长度 与 正常胶囊的最小外接矩形长度
        length, width = capsule_size[ii][0], capsule_size[ii][1]
        info = info + ">>>>长度: {:.2f}".format(length)
        info = info + ">>>>宽度: {:.2f}".format(width)
        if length < nor_len_range[0] or nor_len_range[1] < length:
            is_abnormal = True
        info += ' >> Abnormal \n' if length < nor_len_range[0] or nor_len_range[1] < length else '\n'

        # 检测项目2：瘪壳检测 >> 对比 待测胶囊的轮廓面积 与 健康胶囊的面积
        area = capsule_area[ii]
        info = info + ">>>>面积: {:.2f}".format(area)
        if area < nor_area_range[0] or nor_area_range[1] < area:
            is_abnormal = True
        info += ' >> Abnormal \n' if area < nor_area_range[0] or nor_area_range[1] < area else '\n'

        # 检测项目3：轮廓相似度比较 >> 0~1  越小越相似
        similarity_overall, similarity_head, similarity_tail, = capsule_similarity[ii][0], capsule_similarity[ii][1],capsule_similarity[ii][2],
        info = info + ">>>>与 mask_binary 的轮廓相似度: {:.4f},  {:.4f},  {:.4f}".format(similarity_overall, similarity_head, similarity_tail)
        is_abnormal_similarity = similarity_threshold <= similarity_overall or 1.5 < similarity_head or 1.5 < similarity_tail
        if is_abnormal_similarity:
            is_abnormal = True
        info += ' >> Abnormal !\n' if is_abnormal_similarity else '\n'

        # 检测项目4：局部缺陷检测
        capsule_opened = capsule_set_opened[ii]
        is_defect, max_length = detect_local_defects(capsule_raw, capsule_opened, local_defect_length, ii+1)
        info = info + ">>>>局部缺陷检测最大长度: {:.4f}".format(max_length)
        if is_defect:
            is_abnormal = True
        info += ' >> Abnormal !\n' if is_defect else '\n'

        # 打印状态信息 info
        print(info)
        all_capsule_centers.append(capsule_centers[ii])
        if is_abnormal:
            abnormal_capsule_centers.append(capsule_centers[ii])

        # show_img("{}/{} capsules >> is_abnormal: {}\n L: {}  W: {}  A: {}  S: {:.4f}  DL: {} ".format(ii+1,
        #          len(capsule_set_raw), is_abnormal, int(length),  int(width), int(area), similarity, int(max_length)), capsule_raw)
        L.append(length)
        W.append(width)
        A.append(area)
        S.append(similarity_overall)
    index = []
    index.append(L)
    index.append(W)
    index.append(A)
    index.append(S)
    index = np.array(index)

    return abnormal_capsule_centers, all_capsule_centers


if __name__ == "__main__":
    start_time = time.time()
    img_path = 'data/Figs_0203/002.bmp'
    img_raw = cv2.imread(img_path)
    # show_img("img_raw", img_raw)

    mask_img_path = 'data/Figs_0203/000_mask_raw.png'
    mask_raw = cv2.imread(mask_img_path)
    _, mask_binary = img_preprocessing(mask_raw)

    _, img_opened = img_preprocessing(img_raw)
    new_contours, capsule_set_raw, capsule_set_opened, boxs, capsule_centers, capsule_size, capsule_area, capsule_similarity \
        = find_contours_img(img_raw, img_opened, mask_binary)

    capsule_centers_abnormal, all_capsule_centers = capsule_defect_detection(capsule_set_raw, capsule_set_opened,
                                                                             capsule_centers, capsule_size,
                                                                             capsule_area, capsule_similarity)

    draw_img = img_raw.copy()
    draw_img = cv2.drawContours(draw_img, boxs, -1, (0, 255, 0), 2)
    for center in capsule_centers_abnormal:
        cv2.circle(draw_img, (int(center[0]), int(center[1])), 5, (0, 0, 255), 10)

    for ii in range(len(all_capsule_centers)):
        center = all_capsule_centers[ii]
        cv2.putText(draw_img, str(ii+1), (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 2, (2550, 0, 0), 2)
    show_img("Defection_results", draw_img)

    print('消耗的时间为：',(time.time() - start_time))


