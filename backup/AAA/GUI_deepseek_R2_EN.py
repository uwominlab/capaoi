import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets

from src.params import ROOT_DIR


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
        self.update_rejected_count()

    def initUI(self):
        # Set window properties
        self.setWindowIcon(QIcon(f"{ROOT_DIR}\\backup\\AAA\\logo\\logo.svg"))
        self.setWindowTitle('Capsule Defect Detection GUI')
        self.setGeometry(100, 100, 800, 500)
        self.setFixedSize(800, 500)

        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel layout
        left_panel = QFrame()
        left_panel.setFixedSize(400, 500)
        left_layout = QVBoxLayout(left_panel)

        # Configuration file selection
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Select Configuration File:"))
        self.config_combo = QComboBox()
        self.config_combo.addItem("Please select a configuration file")
        self.load_config_files()
        self.config_combo.currentIndexChanged.connect(self.load_config_parameters)
        config_layout.addWidget(self.config_combo)
        left_layout.addLayout(config_layout)

        # Parameter details display
        params_group = QGroupBox("Configuration Parameters:")
        params_group.setFixedSize(400, 300)
        params_layout = QFormLayout(params_group)
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(3)
        self.param_table.setHorizontalHeaderLabels(["Parameter Name", "Lower Limit", "Upper Limit"])
        self.param_table.setColumnWidth(0, 180)
        self.param_table.setColumnWidth(1, 75)
        self.param_table.setColumnWidth(2, 75)
        params_layout.addWidget(self.param_table)
        left_layout.addWidget(params_group)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.update_config = QPushButton("Update Configuration")
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_detection)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_detection)
        btn_layout.addWidget(self.update_config)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right panel layout
        right_panel = QFrame()
        right_panel.setFixedSize(400, 500)
        right_layout = QVBoxLayout(right_panel)

        # Status bar (time and rejected capsule count)
        status_layout = QHBoxLayout()
        self.time_label = QLabel()
        status_layout.addWidget(QLabel("Time: "))
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()
        self.count_label = QLabel()
        status_layout.addWidget(QLabel("Rejected Capsules: "))
        status_layout.addWidget(self.count_label)
        status_layout.addStretch()
        right_layout.addLayout(status_layout)

        # Image display area
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 300)
        right_layout.addWidget(self.image_label)
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        right_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def load_config_files(self):
        config_dir = f"{ROOT_DIR}\\backup\\AAA\\ConfigFiles"
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith(".txt"):
                    self.config_combo.addItem(file)

    def load_config_parameters(self):
        config_path = f"{ROOT_DIR}\\backup\\AAA\\ConfigFiles\\{self.config_combo.currentText()}"
        if not os.path.exists(config_path):
            return
        self.param_table.setRowCount(0)
        with open(config_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for row, line in enumerate(lines):
                parts = line.strip().split(":")
                if len(parts) == 2:
                    param_name, value = parts[0].strip(), parts[1].strip()
                    min_val, max_val = value.split("-") if "-" in value else ("0", value)
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
        self.param_table.setEditTriggers(QTableWidget.NoEditTriggers if not editable else QTableWidget.AllEditTriggers)

    def load_images(self):
        img_dir = f"{ROOT_DIR}\\backup\\AAA\\Figs"
        self.image_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith(".png")]
        self.current_image_index = 0

    def update_image(self):
        if self.image_files:
            pixmap = QPixmap(self.image_files[self.current_image_index])
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)

    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        QTimer.singleShot(1000, self.update_time)

    def update_rejected_count(self):
        count = 764  # Example count
        self.count_label.setText(str(count))
        QTimer.singleShot(1000, self.update_rejected_count)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CapsuleDetectionGUI()
    window.show()
    sys.exit(app.exec_())
