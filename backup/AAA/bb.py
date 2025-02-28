import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QFileSystemWatcher


class TxtViewer(QWidget):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.initUI()
        self.load_file()

        # 监视文件变化
        self.watcher = QFileSystemWatcher([file_path])
        self.watcher.fileChanged.connect(self.load_file)

    def initUI(self):
        self.setWindowTitle("TXT 参数查看器")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.label = QLabel("参数列表:")
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["参数名称", "值"])

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table_widget)
        self.setLayout(self.layout)

    def load_file(self):
        if not os.path.exists(self.file_path):
            self.table_widget.setRowCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("文件不存在"))
            self.table_widget.setItem(0, 1, QTableWidgetItem(""))
            return

        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            self.table_widget.setRowCount(len(lines))
            for row, line in enumerate(lines):
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        param_name, value = parts[0].strip(), parts[1].strip()
                        self.table_widget.setItem(row, 0, QTableWidgetItem(param_name))
                        self.table_widget.setItem(row, 1, QTableWidgetItem(value))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_path = "C:\\Users\Rui Liu\Desktop\AAA\配置文件\参数文件_胶囊1.txt"  # 你的txt文件路径
    viewer = TxtViewer(file_path)
    viewer.show()
    sys.exit(app.exec_())