import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5 import QtWidgets
import pandas as pd


class CapsuleDetectionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_params = {}
        self.image_files = []
        self.current_image_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.check_for_new_files()
        self.update_time()
        self.update_count()

    def initUI(self):
        # Logo和标题
        self.setWindowIcon(QIcon(r"logo\logo.svg"))
        self.setWindowTitle('胶囊异常检测GUI')

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左侧面板: 布局
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        # 左侧面板: 配置文件选择
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("配置文件选择:"))
        self.config_combo = QComboBox()
        self.config_combo.addItem("请选择配置文件")
        self.load_config_files()
        self.config_combo.currentIndexChanged.connect(self.load_config_param)
        config_layout.addWidget(self.config_combo)
        left_layout.addLayout(config_layout)

        # 左侧面板: 胶囊阈值参数显示区域
        capsule_figure = QGroupBox("胶囊样品展示")  # 创建胶囊图片展示区域
        capsule_figure_layout = QVBoxLayout()

        self.capsule_type_param_box = QLabel()
        # self.capsule_type_param_box = QTextEdit()
        # self.capsule_type_param_box.setReadOnly(True)
        self.capsule_type_param_box.setMaximumHeight(100)  # 设置最大高度 100 piex
        capsule_figure_layout.addWidget(self.capsule_type_param_box)


        self.capsule_figure_zone = QLabel()
        self.capsule_figure_zone.setAlignment(Qt.AlignCenter)  # 让图片居中
        capsule_figure_layout.addWidget(self.capsule_figure_zone)
        capsule_figure.setLayout(capsule_figure_layout)
        left_layout.addWidget(capsule_figure)

        # 参数显示开关
        self.toggle_params_checkbox = QCheckBox("显示配置参数详情")
        self.toggle_params_checkbox.setChecked(False)
        self.toggle_params_checkbox.toggled.connect(self.toggle_params_visibility)
        left_layout.addWidget(self.toggle_params_checkbox)

        # 胶囊参数配置详情
        self.capsule_params_group = QGroupBox("胶囊参数配置详情:")
        self.capsule_params_layout = QFormLayout(self.capsule_params_group)
        self.capsule_param_table = QTableWidget()
        self.capsule_param_table.setColumnCount(3)
        self.capsule_param_table.setHorizontalHeaderLabels(["参数名称", "阈值下限", "阈值上限"])
        self.capsule_param_table.setColumnWidth(0, 180)
        self.capsule_param_table.setColumnWidth(1, 75)
        self.capsule_param_table.setColumnWidth(2, 75)
        self.capsule_params_layout.addWidget(self.capsule_param_table)
        left_layout.addWidget(self.capsule_params_group)

        # 执行器参数配置详情
        self.actuator_params_group = QGroupBox("执行器参数配置详情:")
        self.actuator_params_layout = QFormLayout(self.actuator_params_group)
        self.actuator_param_table = QTableWidget()
        self.actuator_param_table.setColumnCount(2)
        self.actuator_param_table.setHorizontalHeaderLabels(["参数名称", "值"])
        self.actuator_param_table.setColumnWidth(0, 180)
        self.actuator_param_table.setColumnWidth(1, 75)
        self.actuator_params_layout.addWidget(self.actuator_param_table)
        left_layout.addWidget(self.actuator_params_group)

        # 默认不开启
        self.capsule_params_group.setVisible(False)
        self.actuator_params_group.setVisible(False)

        # 左侧面板: 控制按钮
        btn_layout = QHBoxLayout()
        btn_font = QFont("Arial", 12)  # 设置字体为 Arial，大小为 14
        self.update_config_btn = QPushButton("更新配置文件")
        self.update_config_btn.setFont(btn_font)
        self.update_config_btn.clicked.connect(self.update_config_files)

        self.start_btn = QPushButton("开始")
        self.start_btn.setFont(btn_font)
        self.start_btn.clicked.connect(self.start_detection)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setFont(btn_font)
        self.pause_btn.clicked.connect(self.pause_detection)

        btn_layout.addWidget(self.update_config_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        left_layout.addLayout(btn_layout)
        self.btn_setabled(False)

        # 右侧面板：布局
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        # 右侧面板：顶部状态栏
        status_layout = QHBoxLayout()
        # 时间信息
        self.time_label = QLabel()
        status_layout.addWidget(QLabel("时间: "))
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()
        # 剔除胶囊数量信息
        self.count_label = QLabel()
        status_layout.addWidget(QLabel("剔除胶囊粒数: "))
        status_layout.addWidget(self.count_label)
        status_layout.addStretch()

        right_layout.addLayout(status_layout)

        # 右侧面板：图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.image_label)

        # 将左右面板添加到主布局
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # 让窗口根据内容调整大小
        self.adjustSize()

    def load_config_files(self):
        """加载 '配置文件' 目录下的 txt 文件到下拉框"""
        self.config_dir = r"Configuration files"
        if os.path.exists(self.config_dir):
            txt_files = {f for f in os.listdir(self.config_dir) if f.endswith(".txt")}
            self.current_txt_files = txt_files  # 记录当前文件列表
            self.config_combo.clear()
            self.config_combo.addItem("请选择配置文件")  # 默认项
            self.config_combo.addItems(sorted(txt_files))  # 添加排序后的文件名


    def check_for_new_files(self):
        """定期检查 '配置文件' 文件夹，看是否有新 txt 文件"""
        try:
            if os.path.exists(self.config_dir):
                new_txt_files = {f for f in os.listdir(self.config_dir) if f.endswith(".txt")}
                if new_txt_files != self.current_txt_files:
                    self.load_config_files()  # 更新下拉菜单
        except Exception as e:
            print(f"检查新文件时出错: {e}")
        QTimer.singleShot(1000, self.check_for_new_files)


    def load_config_param(self):
        """加载 胶囊样品图片 与 解析参数文件"""
        config_path = f"Configuration files\\{self.config_combo.currentText()}"
        context = self.config_combo.currentText().strip(".txt").split("_")
        capusle_type = context[0] + '_' + context[1]
        capusle_figure_path = f"Configuration files\\Capsule display images\\" + capusle_type + ".png"

        # 加载胶囊型号参数
        def get_attributes_by_type(df, type_value):
            type_value = str(type_value)  # 确保输入值为字符串
            # 查找匹配的行
            row = df[df["Type"] == str(type_value)]
            if row.empty:
                return []
            # 转换为字典返回
            return row.iloc[0].to_dict()

        type_value = context[0]
        type_param_table_path = os.path.join(self.config_dir, 'Capsule type param table.xlsx')
        if os.path.exists(type_param_table_path):
            df = pd.read_excel(type_param_table_path, dtype={"Type": str})
            result = get_attributes_by_type(df, type_value)
        capsule_type_description = ""
        if not result:  # 列表为空
            capsule_type_description = f"Type {type_value} not found"
        else:
            for key, value in result.items():
                capsule_type_description += f"{key}: {value}\n"
        self.capsule_type_param_box.setText(capsule_type_description)



        # 加载配置参数
        if not os.path.exists(config_path) or not os.path.exists(capusle_figure_path):
            self.capsule_figure_zone.clear()
            self.capsule_param_table.setRowCount(0)  # 清空表格内容
            self.actuator_param_table.setRowCount(0)  # 清空表格内容
            QMessageBox.warning(self, "路径或文件缺失", "配置参数表/样品图片 路径不正确或缺失！")
        else:
            # 载入样品图片
            pixmap = QPixmap(capusle_figure_path)
            transform = QTransform().rotate(90)  # 旋转 90°
            pixmap = pixmap.transformed(transform, mode=1)
            scaled_pixmap = pixmap.scaled(self.capsule_figure_zone.size(),  # 适应 QLabel 大小
                                          Qt.KeepAspectRatio,  # 保持图片的长宽比例
                                          Qt.SmoothTransformation)  # 平滑缩放
            self.capsule_figure_zone.setPixmap(scaled_pixmap)
            # 解析配置参数表
            self.capsule_param_table.setRowCount(0)
            self.actuator_param_table.setRowCount(0)
            capsule_row = 0  # 记录执行器参数的行号
            actuator_row = 0  # 记录执行器参数的行号
            with open(config_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for row, line in enumerate(lines):
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        param_name, value = parts[0].strip(), parts[1].strip()
                        if '执行器' not in param_name:
                            if "-" in value:
                                min_val, max_val = value.split("-")
                            else:
                                min_val, max_val = '0', value
                            self.capsule_param_table.insertRow(capsule_row)
                            self.capsule_param_table.setItem(capsule_row, 0, QTableWidgetItem(param_name))
                            self.capsule_param_table.setItem(capsule_row, 1, QTableWidgetItem(min_val))
                            self.capsule_param_table.setItem(capsule_row, 2, QTableWidgetItem(max_val))
                            capsule_row += 1
                        else:
                            self.actuator_param_table.insertRow(actuator_row)
                            self.actuator_param_table.setItem(actuator_row, 0, QTableWidgetItem(param_name))
                            self.actuator_param_table.setItem(actuator_row, 1, QTableWidgetItem(value))
                            actuator_row += 1
            # 设置第一列不可编辑
            for row in range(3):
                item = self.capsule_param_table.item(row, 0)  # 获取第一列的每个单元格
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 移除可编辑标志
            # 设置第一列不可编辑
            for row in range(2):
                item = self.actuator_param_table.item(row, 0)  # 获取第一列的每个单元格
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 移除可编辑标志
        # 解析完参数后，按时 按钮可点击
        self.start_btn.setEnabled(True)


    def start_detection(self):
        self.toggle_editable(False)
        self.load_images()
        self.timer.start(100)
        self.start_btn.setEnabled(False)  # 点击后禁用
        self.pause_btn.setEnabled(True)  # 暂停后开始按钮可用


    def pause_detection(self):
        self.toggle_editable(True)
        self.timer.stop()
        self.start_btn.setEnabled(True)  # 暂停后开始按钮可用
        self.pause_btn.setEnabled(False)  # 暂停后开始按钮可用


    def load_images(self):
        """ 开发阶段读取本地文件夹的图像（若实时接入图像，该函数不需要）"""
        img_dir = r"本地相机图片"
        self.image_files = [os.path.join(img_dir, f)
                            for f in os.listdir(img_dir) if f.endswith(".png")]
        self.current_image_index = 0


    def update_image(self):
        """显示实时采集图片 或 检测结果图片"""
        try:
            if self.image_files:
                pixmap = QPixmap(self.image_files[self.current_image_index])
                scaled_pixmap = pixmap.scaled(self.image_label.size(),  # 适应 QLabel 大小
                                              Qt.KeepAspectRatio,  # 保持长宽比例
                                              Qt.SmoothTransformation)  # 平滑缩放
                self.image_label.setPixmap(scaled_pixmap)
                self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        except Exception as e:
            QMessageBox.warning(self, "路径不存在或不存在jpg文件")


    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        QTimer.singleShot(1000, self.update_time)


    def update_count(self):
        count = 764
        self.count_label.setText(str(count))
        QTimer.singleShot(1000, self.update_count)


    def update_config_files(self):
        """ 更新参数表 获取表格数据并保存为TXT文件 """
        # 创建空列表存储数据
        config_data = []
        # 遍历【胶囊参数】表格，获取参数名 & 值
        for row in range(self.capsule_param_table.rowCount()):
            param_name = self.capsule_param_table.item(row, 0).text()  # 获取参数名称
            min_val = self.capsule_param_table.item(row, 1).text()  # 获取下限值
            max_val = self.capsule_param_table.item(row, 2).text()  # 获取上限值
            txt_content = f"{param_name}:{min_val}-{max_val}"
            print(txt_content)
            config_data.append(txt_content)  # 组合成格式化字符串

        # 遍历【执行器参数】表格，获取参数名 & 值
        for row in range(self.actuator_param_table.rowCount()):
            param_name = self.actuator_param_table.item(row, 0).text()  # 获取参数名称
            value = self.actuator_param_table.item(row, 1).text()  # 获取单一数值
            txt_content = f"{param_name}:{value}"
            print(txt_content)
            config_data.append(txt_content)

        # 打开文件保存对话框
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存配置文件", "", "文本文件 (*.txt);;所有文件 (*.*)", options=options)

        if file_path:  # 确保用户输入了文件名
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write("\n".join(config_data))  # 按行写入数据
                QMessageBox.information(self, "保存成功", f"配置文件已保存至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"发生错误:\n{str(e)}")


    def btn_setabled(self, able):
        if not able:
            self.update_config_btn.setEnabled(False)  # 初始界面，禁用
            self.start_btn.setEnabled(False)  # 初始界面，禁用
            self.pause_btn.setEnabled(False)  # 初始界面，禁用
        else:
            self.update_config_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)


    def toggle_editable(self, editable):
        """切换按钮的可点击状态"""
        self.config_combo.setDisabled(not editable)
        if not editable:
            self.capsule_param_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置不可编辑
            self.actuator_param_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置不可编辑
        else:
            self.capsule_param_table.setEditTriggers(QTableWidget.AllEditTriggers)  # 设置可编辑
            self.actuator_param_table.setEditTriggers(QTableWidget.AllEditTriggers)  # 设置可编辑


    def toggle_params_visibility(self, checked):
        """切换参数表所在布局的可见性"""
        if checked:
            self.show_password_dialog()
        else:
            self.capsule_params_group.hide()  # 使用 hide() 彻底隐藏组件
            self.actuator_params_group.hide()
            self.update_config_btn.setEnabled(False)
        # # 确保 Qt 重新计算布局**
        # self.layout().invalidate()  # 强制 Qt 重新计算布局
        # **强制窗口尺寸更新**
        self.adjustSize()
        # self.resize(self.sizeHint())  # 让窗口能缩小

    def show_password_dialog(self):
        """ 显示密码验证弹窗"""
        password, ok = QInputDialog.getText(self, "密码验证", "请输入密码:", QLineEdit.Password)
        if ok:
            if password == "123456":
                QMessageBox.information(self, "验证成功", "密码正确")
                self.capsule_params_group.setVisible(True)
                self.actuator_params_group.setVisible(True)  # 勾选
                self.update_config_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "验证失败", "密码错误")
                self.toggle_params_checkbox.setChecked(False)  # 取消勾选


    def obtain_screen_resolution(self):
        """获取当前窗口所在的屏幕 """
        current_screen = window.screen()
        # 获取屏幕的分辨率
        screen_geometry = current_screen.geometry()
        dpi = screen_geometry.width() * screen_geometry.height()
        print(dpi)
        return dpi



if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        # ✅ 获取 DPI 缩放比例
        desktop = QApplication.desktop()  # 获取桌面管理器
        screen_num = desktop.screenNumber()  # 获取窗口当前所在的屏幕编号
        screen = desktop.screen(screen_num)  # 获取对应的屏幕
        dpi = screen.logicalDpiX()  # 获取 DPI
        scale_factor = dpi / 96  # 以标准 96 DPI 计算缩放比例
        print('dpi:', dpi, 'scale:', scale_factor)

        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # 让 Qt 进行 DPI 缩放
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # 让图片也进行 DPI 缩放

        window = CapsuleDetectionGUI()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"检查新文件时出错: {e}")