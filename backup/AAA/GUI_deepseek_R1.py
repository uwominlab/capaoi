import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5 import QtWidgets


class CapsuleDetectionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_params = {}
        self.image_files = []
        self.current_image_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.update_time()

    def initUI(self):
        # Logo和标题
        self.setWindowIcon(QIcon(r"C:\Users\Rui Liu\Desktop\AAA\logo\logo.svg"))
        self.setWindowTitle('胶囊异常检测GUI')
        self.setGeometry(100, 100, 1000, 700)
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # 左侧面板
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        # 配置文件选择
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("配置文件选择:"))
        self.config_combo = QComboBox()
        self.config_combo.addItem("请选择配置文件")
        self.load_config_files()
        self.config_combo.currentIndexChanged.connect(self.load_config)
        config_layout.addWidget(self.config_combo)
        left_layout.addLayout(config_layout)

        # 参数显示区域
        params_group = QGroupBox("配置参数详情:")
        params_layout = QFormLayout()

        self.TL_min = QLineEdit()
        self.TL_max = QLineEdit()
        self.TL_min.setAlignment(Qt.AlignRight)
        self.TL_max.setAlignment(Qt.AlignRight)
        params_layout.addRow("轮廓长度阈值 TL(pixel):", self.create_dual_input(self.TL_min, self.TL_max))

        self.TA_min = QLineEdit()
        self.TA_max = QLineEdit()
        self.TA_min.setAlignment(Qt.AlignRight)
        self.TA_max.setAlignment(Qt.AlignRight)
        params_layout.addRow("轮廓面积阈值 TA(pixel):", self.create_dual_input(self.TA_min, self.TA_max))

        self.TSF = QLineEdit()
        self.TSF.setAlignment(Qt.AlignRight)
        params_layout.addRow("整体轮廓相似度阈值 TST:", self.TSF)

        self.TSH = QLineEdit()
        self.TSH.setAlignment(Qt.AlignRight)
        params_layout.addRow("头部轮廓相似度阈值 TSH:", self.TSH)

        self.TDL = QLineEdit()
        self.TDL.setAlignment(Qt.AlignRight)
        params_layout.addRow("局部缺陷长度阈值 TDL(pixel):", self.TDL)

        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.update_config = QPushButton("更新配置")
        # self.update_config.clicked.connect(self.update_config_files)
        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self.start_detection)
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_detection)
        btn_layout.addWidget(self.update_config)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        left_layout.addLayout(btn_layout)

        # 右侧面板
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        # 顶部状态栏
        status_layout = QHBoxLayout()
        self.time_label = QLabel()
        status_layout.addWidget(QLabel("时间:"))
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()

        self.pixel_label = QLabel("像素: 1440×2560")
        status_layout.addWidget(self.pixel_label)

        self.count_label = QLabel("剔除胶囊粒数: 764")
        status_layout.addWidget(self.count_label)
        # self.cpsule_count_remove = 764
        # status_layout.addRow("剔除胶囊粒数:", self.cpsule_count_remove)

        status_layout.addWidget(self.count_label)

        right_layout.addLayout(status_layout)

        # 图片显示区域
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(800, 600)
        right_layout.addWidget(self.image_label)

        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        # 窗口控制按钮
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.addStretch()
        min_btn = QPushButton("－")
        close_btn = QPushButton("×")
        min_btn.clicked.connect(self.showMinimized)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(close_btn)
        self.setMenuWidget(title_widget)

    def create_dual_input(self, *widgets):
        container = QWidget()
        layout = QHBoxLayout(container)
        for w in widgets:
            layout.addWidget(w)
        return container

    def load_config_files(self):
        config_dir = r"C:\Users\Rui Liu\Desktop\AAA\配置文件"
        if os.path.exists(config_dir):
            for f in os.listdir(config_dir):
                if f.endswith(".txt"):
                    self.config_combo.addItem(f)

    def load_config(self):
        filename = self.config_combo.currentText()
        filepath = os.path.join(r"C:\Users\Rui Liu\Desktop\AAA\配置文件", filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':')
                        key = key.strip()  # 移除收尾首尾空格
                        if '-' in value:
                            min_val, max_val = value.strip().split('-')
                            if 'TL' in key:
                                self.TL_min.setText(min_val)
                                self.TL_max.setText(max_val)
                            elif 'TA' in key:
                                self.TA_min.setText(min_val)
                                self.TA_max.setText(max_val)
                        else:
                            if 'TST' in key:
                                self.TSF.setText(value.strip())
                            elif 'TSH' in key:
                                self.TSH.setText(value.strip())
                            elif 'TDL' in key:
                                self.TDL.setText(value.strip())
        except Exception as e:
            QMessageBox.warning(self, "错误", f"配置文件读取失败: {str(e)}")

    def start_detection(self):
        self.toggle_editable(False)
        self.load_images()
        self.timer.start(100)

    def pause_detection(self):
        self.toggle_editable(True)
        self.timer.stop()

    def toggle_editable(self, editable):
        for w in [self.TL_min, self.TL_max, self.TA_min, self.TA_max,
                  self.TSF, self.TSH, self.TDL]:
            w.setReadOnly(not editable)
        self.config_combo.setDisabled(not editable)

    def load_images(self):
        img_dir = r"C:\Users\Rui Liu\Desktop\AAA\Figs"
        self.image_files = [os.path.join(img_dir, f)
                            for f in os.listdir(img_dir) if f.endswith(".png")]
        self.current_image_index = 0

    def update_image(self):
        try:
            if self.image_files:
                pixmap = QPixmap(self.image_files[self.current_image_index])
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.size(), Qt.KeepAspectRatio))
                self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        except Exception as e:
            QMessageBox.warning(self, "路径不存在或不粗在jpg文件")

    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        QTimer.singleShot(1000, self.update_time)

    def update_config_files(self):
        return None




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CapsuleDetectionGUI()
    window.show()
    sys.exit(app.exec_())