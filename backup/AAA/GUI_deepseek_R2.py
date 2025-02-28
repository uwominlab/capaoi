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
        self.update_count()

    def initUI(self):
        # Logo和标题
        self.setWindowIcon(QIcon(r"C:\Users\Rui Liu\Desktop\AAA\logo\logo.svg"))
        self.setWindowTitle('胶囊异常检测GUI')
        self.setGeometry(100, 100, 700, 500)
        self.setFixedSize(800, 500)
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # 左侧面板: 布局
        left_panel = QFrame()
        left_panel.setFixedSize(400, 500)
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

        # 左侧面板: 阈值参数显示区域
        params_group = QGroupBox("配置参数详情:")
        params_group.setFixedSize(400, 300)  # 设置宽度为 200 px，高度为 100 px
        params_layout = QFormLayout(params_group)
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(3)
        self.param_table.setHorizontalHeaderLabels(["参数名称", "阈值下限", "阈值上限"])
        self.param_table.setColumnWidth(0, 180)  # 第一列宽度设为 250
        self.param_table.setColumnWidth(1, 75)  # 第二列宽度设为 100
        self.param_table.setColumnWidth(2, 75)  # 第三列宽度设为 100
        params_layout.addWidget(self.param_table)
        left_layout.addWidget(params_group)

        # 左侧面板: 控制按钮
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
        # 左侧布局中，多个容器严格从上到下紧凑分布，不因窗口变小/变大而压缩或拉伸！
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 右侧面板：布局
        right_panel = QFrame()
        right_panel.setFixedSize(400, 500)
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
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 300)
        right_layout.addWidget(self.image_label)
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        # 右侧布局中，多个容器严格从上到下紧凑分布，不因窗口变小/变大而压缩或拉伸！
        right_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

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

    def load_config_param(self):
        config_path = f"C:\\Users\\Rui Liu\\Desktop\\AAA\\配置文件\\{self.config_combo.currentText()}"
        if not os.path.exists(config_path):
            return
        self.param_table.setRowCount(0)
        with open(config_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for row, line in enumerate(lines):
                parts = line.strip().split(":")
                if len(parts) == 2:
                    param_name, value = parts[0].strip(), parts[1].strip()
                    if "-" in value:
                        min_val, max_val = value.split("-")
                    else:
                        min_val, max_val = 0, value
                    self.param_table.insertRow(row)
                    self.param_table.setItem(row, 0, QTableWidgetItem(param_name))
                    self.param_table.setItem(row, 1, QTableWidgetItem(min_val))
                    self.param_table.setItem(row, 2, QTableWidgetItem(max_val))

    def start_detection(self):
        self.toggle_editable(False)
        self.load_images()
        self.timer.start(100)

    def pause_detection(self):
        self.toggle_editable(True)
        self.timer.stop()

    def toggle_editable(self, editable):
        self.config_combo.setDisabled(not editable)
        if not editable:
            self.param_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置不可编辑
        else:
            self.param_table.setEditTriggers(QTableWidget.AllEditTriggers)  # 设置可编辑

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
            QMessageBox.warning(self, "路径不存在或不存在jpg文件")

    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        QTimer.singleShot(1000, self.update_time)

    def update_count(self):
        count = 764
        self.count_label.setText(str(count))
        QTimer.singleShot(1000, self.update_count)

    def update_config_files(self):
        # """ 获取表格数据并保存为 TXT 文件 """
        # options = QFileDialog.Options()
        # file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt);;所有文件 (*)", options=options)
        #
        # if file_path:
        #     with open(file_path, 'w', encoding='utf-8') as file:
        #         row_count = self.table.rowCount()
        #         col_count = self.table.columnCount()
        # 
        #         for row in range(row_count):
        #             row_data = []
        #             for col in range(col_count):
        #                 item = self.table.item(row, col)
        #                 row_data.append(item.text() if item else "")  # 处理空单元格
        #             file.write("\t".join(row_data) + "\n")  # 用 TAB 分隔列数据

            # print(f"数据已保存到 {file_path}")




        return None




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CapsuleDetectionGUI()
    window.show()
    sys.exit(app.exec_())