import sys
import os
import time
import re
from PyQt5 import QtWidgets, QtGui, QtCore


class CapsuleInspectionGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.param_fields = {}  # 先初始化参数字段
        self.initUI()
        self.image_list = []
        self.image_index = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_image)

    def initUI(self):
        self.setWindowTitle("胶囊异常检测GUI")
        self.setGeometry(100, 100, 900, 500)

        # Layouts
        main_layout = QtWidgets.QHBoxLayout(self)
        left_layout = QtWidgets.QVBoxLayout()
        right_layout = QtWidgets.QVBoxLayout()

        # Logo and Title
        logo_label = QtWidgets.QLabel()
        logo_pixmap = QtGui.QPixmap("C:\\Users\\Rui Liu\\Desktop\\新建文件夹\\logo\\logo.svg")
        logo_label.setPixmap(logo_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio))
        title_label = QtWidgets.QLabel("胶囊异常检测GUI")
        title_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(logo_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        # Time Display
        self.time_label = QtWidgets.QLabel()
        self.update_time()
        self.time_timer = QtCore.QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

        top_layout.addWidget(QtWidgets.QLabel("时间:"))
        top_layout.addWidget(self.time_label)

        left_layout.addLayout(top_layout)

        # Config File Selection
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(QtWidgets.QLabel("配置文件:"))
        self.config_combobox = QtWidgets.QComboBox()
        self.load_config_files()
        self.config_combobox.currentIndexChanged.connect(self.load_config)
        config_layout.addWidget(self.config_combobox)
        left_layout.addLayout(config_layout)

        # Parameter Display
        param_layout = QtWidgets.QVBoxLayout()

        threshold_data = {
            "轮廓长度阈值TL(pixel)": ["", ""],
            "轮廓面积阈值TA(pixel)": ["", ""]
        }

        for label, values in threshold_data.items():
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            field_min = QtWidgets.QLineEdit(values[0])
            field_max = QtWidgets.QLineEdit(values[1])
            row.addWidget(field_min)
            row.addWidget(QtWidgets.QLabel("~"))
            row.addWidget(field_max)
            self.param_fields[label] = (field_min, field_max)
            param_layout.addLayout(row)

        other_params = {
            "整体轮廓相似度阈值TST": "",
            "头部轮廓相似度阈值TSH": "",
            "局部缺陷长度阈值TDL(pixel)": ""
        }

        for label, value in other_params.items():
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            field = QtWidgets.QLineEdit(value)
            row.addWidget(field)
            self.param_fields[label] = field
            param_layout.addLayout(row)

        left_layout.addLayout(param_layout)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.update_btn = QtWidgets.QPushButton("更新配置")
        # self.update_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.update_btn)

        self.start_btn = QtWidgets.QPushButton("开始")
        self.start_btn.clicked.connect(self.start_inspection)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QtWidgets.QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_inspection)
        btn_layout.addWidget(self.pause_btn)

        left_layout.addLayout(btn_layout)

        # Image Display
        self.image_label = QtWidgets.QLabel()
        right_layout.addWidget(self.image_label)

        # Image Info
        self.capsule_count_label = QtWidgets.QLabel("剔除胶囊粒数: 764")
        self.resolution_label = QtWidgets.QLabel("像素: ")
        right_layout.addWidget(self.capsule_count_label)
        right_layout.addWidget(self.resolution_label)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

    def load_config_files(self):
        config_dir = "C:\\Users\\Rui Liu\\Desktop\\新建文件夹\\配置文件\\"
        if os.path.exists(config_dir):
            files = [f for f in os.listdir(config_dir) if f.endswith(".txt")]
            self.config_combobox.addItems(files)
            if files:
                self.load_config()

    def load_config(self):
        config_dir = "C:\\Users\\Rui Liu\\Desktop\\新建文件夹\\配置文件\\"
        file_name = self.config_combobox.currentText()
        file_path = os.path.join(config_dir, file_name)

        if not os.path.exists(file_path):
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = file.readlines()

        for line in data:
            match = re.match(r"(.+?)：(\d+)(?:~(\d+))?", line.strip())
            if match:
                key, val1, val2 = match.groups()
                if key in self.param_fields:
                    if isinstance(self.param_fields[key], tuple):
                        self.param_fields[key][0].setText(val1)
                        self.param_fields[key][1].setText(val2 if val2 else "")
                    else:
                        self.param_fields[key].setText(val1)

    def update_time(self):
        current_time = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.time_label.setText(current_time)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = CapsuleInspectionGUI()
    gui.show()
    sys.exit(app.exec_())
