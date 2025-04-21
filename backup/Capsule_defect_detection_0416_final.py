import cv2
import numpy as np
import imutils
import time
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams['figure.dpi'] = 300   # 图形的DPI


def show_img(img_name, img):
    if len(img_raw.shape)==3:
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
    # step 1: 灰度化  注意原始图像img_raw的RGB通道顺序
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)   # 图像灰度化
    # show_img("img_gray", img_gray)
    # step 1: 噪点抑制
    img_gray = cv2.medianBlur(img_gray, 15)  # 中值滤波：去椒盐噪声+保边缘
    # show_img("img_gray", img_gray)
    # img_gray = cv2.GaussianBlur(img_gray, (5,5), 0)  # 高斯滤波：平滑图像
    # show_img("img_gray", img_gray)
    ## step 3: 二值化  黑色RGB>>[0,0,0]   白色RGB>>[225,255,255]
    _, img_binary = cv2.threshold(img_gray, 100, 255, cv2.THRESH_BINARY)  # 图像二值化， 阈值=165（阈值影响开闭运算效果）
    img_binary = cv2.inRange(img_gray, 1, 255)  # 提取浅色胶囊
    # show_img("img_binary", img_binary)
    # step 4: 形态学操作：先腐蚀再膨胀，去小噪点（等效与开运算）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))   # 定义矩形结构元素，核尺寸最好为奇数
    img_opened = cv2.morphologyEx(img_binary, cv2.MORPH_OPEN, kernel, iterations=1)  # 闭运算（链接块）
    # show_img("img_opened", img_opened)
    return img_raw, img_opened


def calculate_contours_similarity(target_opened, contour_mask):
    """
    :param target_opened: 分割出来的胶囊图像的二值化图像（开运算后）
    :param contour_mask: 正常胶囊制作的 mask (二值化图像)
    :return:
    """
    # 输入图像（二值图像，黑色作为背景，白色作为目标），轮廓检索方式
    contours = cv2.findContours(target_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本
    # Take the largest contour as the main contour
    main_contour = max(contours, key=cv2.contourArea)  # 提取主轮廓
    similarity = cv2.matchShapes(contour_mask, main_contour, cv2.CONTOURS_MATCH_I1, 0.0)
    return main_contour, similarity


def find_contours_img(img_raw, img_opened, mask_binary):
    """
    :param img_raw: 原始图像
    :param img_opened: 原始图像的二值化（开运算后）
    :param mask_binary: 正常胶囊制作的 mask (二值化图像)
    :return:
       new_contours         裁剪后胶囊的新轮廓(裁剪后，像素变少，原来求的轮廓不在适用)
       capsule_set_raw      图像裁剪后，胶囊的原始图像
       capsule_set_opened   图像裁剪后，胶囊的去噪图像
       rects:               胶囊的最小外接矩形 info: rect_center, rect_scale, rotation_angle
       boxs:                胶囊的最小外接矩形的顶点
       centers:             胶囊在原始图像中的像素中心
    """
    # 输入图像（二值图像，黑色作为背景，白色作为目标），轮廓检索方式
    contours = cv2.findContours(img_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = imutils.grab_contours(contours)  # 适配不同的 opencv 版本
    # 提取有效轮廓：如果某物体轮廓点数量位于阈值区间，则认为是 胶囊
    contours = [c for c in contours if 400 < c.shape[0] < 1500]

    # 轮廓排序（从上往下、从右往左）：获取轮廓边界框（x, y, w, h），然后y坐标升序排序， x坐标降序排序
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    contours = sorted(contours, key=lambda c: (-cv2.boundingRect(c)[0], cv2.boundingRect(c)[1]))
    # img_raw_copy = img_raw.copy()
    # cv2.drawContours(img_raw_copy, contours, -1, (0, 0, 255), 2)
    # show_img("contour_defection_results", img_raw_copy)

    rects, boxs, capsule_centers = [], [], []
    for contour in contours:
        # 求有效轮廓的最小外接矩形, 返回 center(x,y), (width, height), angle of rotation
        rect = cv2.minAreaRect(contour)
        capsule_centers.append(rect[0])
        rects.append(rect)  # rect >> rect_center, rect_scale, rotation_angle
        box = np.int64(cv2.boxPoints(rect))  # 通过函数cv2.boxPoints获得绘制这个矩形需要矩形的4个角点
        boxs.append(box)
    draw_img = cv2.drawContours(img_raw.copy(), boxs, -1, (0, 0, 255), 2)
    # for center in capsule_centers:
    #     cv2.circle(draw_img, (int(center[0]), int(center[1])), 10, (0, 0, 255), 10)
    #     show_img("contour_defection_results", draw_img)

    # 导入标准胶囊的轮廓 mask
    mask_overall = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_head = cv2.findContours(mask_binary[:int(0.20 * mask_binary.shape[0]), :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_tail = cv2.findContours(mask_binary[int(0.80 * mask_binary.shape[0]):, :], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask_overall, mask_head, mask_tail = (imutils.grab_contours(mask_overall),
                                          imutils.grab_contours(mask_head), imutils.grab_contours(mask_tail))
    mask_overall, mask_head, mask_tail = mask_overall[0], mask_head[0], mask_tail[0]
    # show_img("mask_overall", mask_binary)
    # show_img("mask_head", mask_binary[:int(0.20*mask_binary.shape[0]), :])
    # show_img("mask_tail", mask_binary[int(0.80*mask_binary.shape[0]):, :])

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
        length, width = np.max(rects[ii][1]), np.min(rects[ii][1])
        # 整体轮廓相似度, 胶囊头部、尾部相似度, 面积
        main_contour, similarity_overall = calculate_contours_similarity(target_opened, mask_overall)
        _, similarity_head = calculate_contours_similarity(target_opened[:int(0.20*target_opened.shape[0]), :], mask_head)
        _, similarity_tail = calculate_contours_similarity(target_opened[int(0.80*target_opened.shape[0]):, :], mask_tail)
        area = cv2.contourArea(main_contour)
        # show_img("{}/{} capsule overall >> {:.4f}".format(ii + 1, len(rects), similarity_overall), target_opened)
        # show_img("{}/{} capsule head >> {:.4f}".format(ii + 1, len(rects), similarity_head), target_opened[:int(0.20*target_opened.shape[0]), :])
        # show_img("{}/{} capsule tail >> {:.4f}".format(ii + 1, len(rects), similarity_tail), target_opened[int(0.80*target_opened.shape[0]):, :])

        capsule_size.append(np.array([length, width]))
        capsule_area.append(area)
        capsule_similarity.append([similarity_overall, similarity_head, similarity_tail])
        # target_raw_copy = target_raw.copy()
        # cv2.drawContours(target_raw_copy, contours, -1, (0, 255, 0), 3)
        # show_img("{}/{} capsules >> L: {:.2f} W: {:.2f} Area: {}".format(ii+1, len(rects), length, width, area), target_raw_copy)
        # show_img("{}/{} capsules: ".format(ii+1, len(rects)), target_opened)

    return new_contours, capsule_set_raw, capsule_set_opened, boxs, capsule_centers, capsule_size, capsule_area, capsule_similarity



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



def capsule_defect_detection(capsule_set_raw, capsule_set_opened,  capsule_centers, capsule_size, capsule_area, capsule_similarity,
                             nor_len_range=[310, 330], nor_width_range=[100, 150], nor_area_range=[30500, 35000],
                             similarity_threshold_overall=0.1, similarity_threshold_head=0.3, local_defect_length=75):
    """
    :param capsule_set_raw:    胶囊的裁剪图 原图
    :param capsule_set_opened: 胶囊的裁剪 二值图
    :param capsule_centers:    胶囊的在capsule_set_raw中的中心坐标
    :param capsule_size:       胶囊的尺寸
    :param capsule_area:       胶囊面积
    :param capsule_similarity: 胶囊的相似度
    :param nor_len_range:      正常长度范围（范围内为正常）
    :param nor_area_range:     正常面积范围（范围内为正常）
    :param similarity_threshold_overall: 整体相似度阈值（低于阈值为正常）
    :param similarity_threshold_head:    头部相似度阈值（低于阈值为正常）
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
        is_abnormal_similarity = similarity_threshold_overall <= similarity_overall or similarity_threshold_head < similarity_head or 0.3 < similarity_threshold_head
        if is_abnormal_similarity:
            is_abnormal = True
        info += ' >> Abnormal !\n' if is_abnormal_similarity else '\n'

        # 检测项目4：局部缺陷检测
        capsule_opened = capsule_set_opened[ii]
        is_defect, max_length = detect_local_defects(capsule_raw, capsule_opened, length, width, local_defect_length, ii+1)
        info = info + ">>>>局部缺陷检测最大长度: {:.4f}".format(max_length)
        if is_defect:
            is_abnormal = True
        info += ' >> Abnormal !\n' if is_defect else '\n'

        # 打印状态信息 info
        print(info)
    #     all_capsule_centers.append(capsule_centers[ii])
    #     if is_abnormal:
    #         abnormal_capsule_centers.append(capsule_centers[ii])
    #     L.append(length)
    #     W.append(width)
    #     A.append(area)
    #     S.append(similarity_overall)
    # index = []
    # index.append(L)
    # index.append(W)
    # index.append(A)
    # index.append(S)
    # index = np.array(index)

    return abnormal_capsule_centers, all_capsule_centers


def remove_bgc(img, bgc_ranges):
    img_cvt = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    for color_name, (lower, upper) in bgc_ranges.items():
        lower = np.array(lower, dtype="uint8")
        upper = np.array(upper, dtype="uint8")
        # 生成掩码
        mask = cv2.inRange(img_cvt, lower, upper)
        inverted_mask = cv2.bitwise_not(mask)
        # 结果图像
        result = cv2.bitwise_and(img, img, mask=inverted_mask)
    # result = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return result






if __name__ == "__main__":
    start_time = time.time()
    # 1型胶囊 参数
    # img_path = 'Figs_0203/1_Capsule_2.bmp'
    # img_raw = cv2.imread(img_path)
    # show_img("img_raw", img_raw)
    # _, img_opened = img_preprocessing(img_raw)
    # mask_img_path = 'Configuration files/Capsule display images/1_Capsule.png'
    # mask_raw = cv2.imread(mask_img_path)
    # _, mask_opened = img_preprocessing(mask_raw)
    #
    # nor_len_range = [310, 330]
    # nor_area_range = [30500, 35000]
    # similarity_threshold_overall = 0.1
    # similarity_threshold_head = 0.3
    # local_defect_length = 75

    # 00型胶囊
    # img_path = 'Figs_0203/1_Capsule_7.bmp'
    # img_path = 'Color selection2/3.jpg'
    # bgc_ranges = {"bgc": ([20, 50, 100], [150, 150, 220])}  # 蓝色
    # img_path = 'Color selection2/4.jpg'  # 青色背景
    # bgc_ranges = {"bgc": ([10, 75, 45], [120, 200, 170])}  # 青色
    # img_path = 'Color selection2/13.jpg'  # 天蓝色背景
    # bgc_ranges = {"bgc": ([0, 30, 60], [120, 190, 220])}  # 天蓝色

    # img_path = 'Color selection0410/0.bmp'  # 黑色背景
    # bgc_ranges = {"bgc": ([0, 0, 0], [100, 100, 100])}  # 黑色

    # img_path = 'Color selection0410/1.bmp'  # 黑色背景
    # bgc_ranges = {"bgc": ([0, 0, 0], [80, 80, 80])}  # 黑色

    img_path = 'Color selection0410/2.bmp'  # 天蓝色背景
    bgc_ranges = {"bgc": ([0, 30, 60], [120, 190, 220])}  # 天蓝色  [90， 160， 160]

    # img_path = 'Color selection0410/5.bmp'  # 天蓝色背景
    # bgc_ranges = {"bgc": ([0, 0, 0], [120, 190, 220])}  # 天蓝色  [90， 160， 160]

    # img_path = 'Color selection0410/4.bmp'  # 天蓝色背景
    # bgc_ranges = {"bgc": ([0, 0, 0], [120, 190, 220])}  # 天蓝色  [90， 160， 160]

    img_raw = cv2.imread(img_path)
    img_raw_rbg = remove_bgc(img=img_raw, bgc_ranges=bgc_ranges)
    show_img("img_raw", img_raw)
    show_img("img_raw_rbg", img_raw_rbg)

    img_raw = img_raw_rbg
    _, img_opened = img_preprocessing(img_raw)
    show_img("img_opened", img_opened)
    # mask_img_path = 'Configuration files/Capsule display images/00_Capsule.png'
    # mask_raw = cv2.imread(mask_img_path)
    # _, mask_opened = img_preprocessing(mask_raw)
    # show_img("mask_opened", mask_opened)
    mask_img_path = 'Configuration files/Capsule display images/Capsule_1_mask_binary.png'
    mask_opened = cv2.imread(mask_img_path, cv2.IMREAD_GRAYSCALE)
    # show_img("mask_opened", mask_opened)

    new_contours, capsule_set_raw, capsule_set_opened, boxs, capsule_centers, \
        capsule_size, capsule_area, capsule_similarity = find_contours_img(img_raw, img_opened, mask_opened)

    nor_len_range = [375, 400]
    nor_area_range = [46000, 49000]
    similarity_threshold_overall = 0.7
    similarity_threshold_head = 0.3
    local_defect_length = 75
    capsule_centers_abnormal, all_capsule_centers = capsule_defect_detection(capsule_set_raw, capsule_set_opened, capsule_centers,
                                                                             capsule_size, capsule_area, capsule_similarity,
                                                                             nor_len_range=nor_len_range, nor_area_range=nor_area_range,
                                                                             similarity_threshold_overall=similarity_threshold_overall,
                                                                             similarity_threshold_head=similarity_threshold_head,
                                                                             local_defect_length=local_defect_length)
    print('消耗的时间为：',(time.time() - start_time))

    # draw_img = img_raw.copy()
    # draw_img = cv2.drawContours(draw_img, boxs, -1, (0, 255, 0), 2)
    #
    # for center in capsule_centers_abnormal:
    #     cv2.circle(draw_img, (int(center[0]), int(center[1])), 5, (0, 0, 255), 10)
    #
    # for ii in range(len(all_capsule_centers)):
    #     center = all_capsule_centers[ii]
    #     cv2.putText(draw_img, str(ii+1), (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 2, (2550, 0, 0), 2)
    # show_img("Defection_results", draw_img)




