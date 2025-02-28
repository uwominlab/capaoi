from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QLabel, QSpacerItem, QSizePolicy

class CompactContainerDemo(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QFrame 多个容器紧凑排列")
        self.setGeometry(100, 100, 400, 300)

        # 创建 QFrame 容器（主框架）
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Box)

        # 创建 QVBoxLayout（垂直布局）
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 设置内边距
        layout.setSpacing(5)  # 控件之间的间距（可以调整）

        # 添加多个子容器（这里用 QFrame 模拟）
        sub_frame1 = self.create_sub_frame("子容器 1", 50)
        sub_frame2 = self.create_sub_frame("子容器 2", 80)
        sub_frame3 = self.create_sub_frame("子容器 3", 60)

        layout.addWidget(sub_frame1)
        layout.addWidget(sub_frame2)
        layout.addWidget(sub_frame3)

        # **关键：添加一个弹性填充，使子容器始终紧贴顶部**
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 设置 QFrame 的布局
        frame.setLayout(layout)

        # 主窗口布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(frame)
        main_layout.addStretch()  # 防止 QFrame 自身也被拉伸
        self.setLayout(main_layout)

    def create_sub_frame(self, text, height):
        """ 创建一个子容器（QFrame），内部带一个 QLabel """
        sub_frame = QFrame()
        sub_frame.setFrameShape(QFrame.Box)
        sub_frame.setFixedHeight(height)  # 固定高度，防止自动拉伸

        sub_layout = QVBoxLayout(sub_frame)
        label = QLabel(text, sub_frame)
        sub_layout.addWidget(label)

        return sub_frame

if __name__ == "__main__":
    app = QApplication([])
    window = CompactContainerDemo()
    window.show()
    app.exec_()
