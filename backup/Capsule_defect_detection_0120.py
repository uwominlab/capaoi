import cv2
import numpy as np
import imutils
import time
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams['figure.dpi'] = 300   # 图形的DPI


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
    draw_img = cv2.drawContours(img_raw.copy(), boxs, -1, (0, 0, 255), 2)
    for center in capsule_centers:
        cv2.circle(draw_img, (int(center[0]), int(center[1])), 10, (0, 0, 255), 10)
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

        # 如果纵向排布，变成横向
        if target_raw.shape[0] > target_raw.shape[1]:
            target_raw = cv2.rotate(target_raw, cv2.ROTATE_90_CLOCKWISE)
            target_opened = cv2.rotate(target_opened, cv2.ROTATE_90_CLOCKWISE)
        capsule_set_raw.append(target_raw)
        capsule_set_opened.append(target_opened)

        # 胶囊参数计算：长度length  宽度width  面积area
        contours = cv2.findContours(target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 输入图像（二值图像，黑色作为背景，白色作为目标），轮廓检索方式，
        contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本
        contours = sorted(contours, key=len, reverse=True)
        new_contours.append(contours[0])

        length, width = np.max(rects[ii][1]), np.min(rects[ii][1][1])
        area = cv2.contourArea(contours[0])
        similarity = cv2.matchShapes(contours_mask, contours[0], 1, 0.0)

        capsule_size.append(np.array([length, width]))
        capsule_area.append(area)
        capsule_similarity.append(similarity)
        target_raw_copy = target_raw.copy()
        cv2.drawContours(target_raw_copy, contours, -1, (0, 255, 0), 3)
        show_img("{}/{} capsules >> L: {:.2f} W: {:.2f} Area: {}".format(ii+1, len(rects), length, width, area), target_raw_copy)
        # show_img("{}/{} capsules: ".format(ii+1, len(rects)), target_opened)

    return new_contours, capsule_set_raw, capsule_set_opened, rects, capsule_centers, capsule_size, capsule_area, capsule_similarity



def detect_local_defects(capsule_raw, capsule_opened):
    # (原图掩膜操作>>均值滤波>>滤波图像原图进行差分>>二值化>>查找轮廓(根据轮廓长度进行筛选)
    draw_image = capsule_raw.copy()
    capsule_masked = cv2.bitwise_and(draw_image, draw_image, mask=capsule_opened)  # 对原始图像进行掩码运算
    # show_img("capsule_masked", capsule_masked)
    # 截取胶囊中部视角
    window = [int(0.35 * capsule_masked.shape[1]), int(0.65 * capsule_masked.shape[1])]
    capsule_masked = capsule_masked[:, window[0]: window[1], :]
    # show_img("capsule_masked", capsule_masked)

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
    for i in range(0, len(contours)):
        length = cv2.arcLength(contours[i], True)
        # info = info + ">>>>局部缺陷长度: {}".format(length)
        # 通过轮廓长度筛选
        if 100 < length:
            is_defect = True
            cv2.drawContours(img2, contours[i], -1, (0, 0, 255), 2)
            show_img("local_defects", img2)

    return is_defect





def capsule_defect_detection(capsule_set_raw, capsule_set_opened,  capsule_centers, capsule_size, capsule_area, capsule_similarity,
                             nor_len_range=[310, 320], nor_area_range=[30500, 32000]):
    """
    :param capsule_set_raw:    胶囊的裁剪图 原图
    :param capsule_set_opened: 胶囊的裁剪 二值图
    :param rects:  胶囊的最小外接矩形 info: rect_center, rect_scale, rotation_angle
    :param boxs:  胶囊的最小外接矩形的顶点
    :param nor_len_range: 正常长度范围

    :return:
    """
    centers_abnormal_capsule = []

    for ii in range(0, len(capsule_set_raw)):
        capsule_raw = capsule_set_raw[ii]
        info = "{} of {} capsules: \n".format(ii + 1, len(capsule_set_raw))
        result_flag = 0

        # 检测项目1：长度检测 >> 对比 待测胶囊的最小外接矩形长度 与 正常胶囊的最小外接矩形长度
        length, width = capsule_size[ii][0], capsule_size[ii][1]
        info = info + ">>>>长度: {}".format(length)
        if length < nor_len_range[0] or nor_len_range[1] < length:
            result_flag = 1
        info += ' >> Abnormal \n' if length < nor_len_range[0] or nor_len_range[1] < length else '\n'

        # 检测项目2：瘪壳检测 >> 对比 待测胶囊的轮廓面积 与 健康胶囊的面积
        area = capsule_area[ii]
        info = info + ">>>>面积: {}".format(area)
        if area < nor_area_range[0] or nor_area_range[1] < area:
            result_flag = 1
        info += ' >> Abnormal \n' if area < nor_area_range[0] or nor_area_range[1] < area else '\n'

        # 检测项目3：轮廓相似度比较 >> 0~1  越小越相似
        similarity = capsule_similarity[ii]
        info = info + ">>>>与 mask_binary 的轮廓相似度: {}".format(similarity)
        if 0.1 < similarity:
            result_flag = 1
        info += ' >> Abnormal !\n' if 0.1 < similarity else '\n'

        # 检测项目4：局部缺陷检测
        capsule_opened = capsule_set_opened[ii]
        info = info + ">>>>局部缺陷: {}".format(similarity)
        is_defect = detect_local_defects(capsule_raw, capsule_opened)
        if is_defect:
            result_flag = 1
        info += ' >> Abnormal !\n' if result_flag else '\n'

        # 打印状态信息 info
        print(info)
        # cv2.putText(draw_image, 'Result flag: '+ str(result_flag), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
        # show_img("{}/{} capsules".format(ii, len(capsule_set_raw)), draw_image)

        if result_flag == 1:
            centers_abnormal_capsule.append(capsule_centers[ii])

    return centers_abnormal_capsule


if __name__ == "__main__":
    start_time = time.time()
    # img_path = 'Figs_14/006.bmp'
    img_path = 'Figs_30/001.bmp'
    # img_path = 'Figs_14/007.jpg'
    img_raw = cv2.imread(img_path)
    # img_raw = img_raw[:, 1300: 2200:, :]
    # img_raw = np.transpose(img_raw, (1, 0, 2))
    # show_img("img_raw", img_raw)

    mask_img_path = 'Figs/000_mask_raw.png'
    mask_raw = cv2.imread(mask_img_path)
    _, mask_binary = img_preprocessing(mask_raw)

    img_raw, img_opened = img_preprocessing(img_raw)
    new_contours, capsule_set_raw, capsule_set_opened, rects, capsule_centers, capsule_size, capsule_area, capsule_similarity \
        = find_contours_img(img_raw, img_opened, mask_binary)

    capsule_centers_abnormal = capsule_defect_detection(capsule_set_raw, capsule_set_opened, capsule_centers, capsule_size, capsule_area, capsule_similarity,)

    print('消耗的时间为：',(time.time() - start_time))


