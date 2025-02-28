import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer

class ImageViewer(QWidget):
    def __init__(self, image_folder):
        super().__init__()

        self.image_folder = image_folder
        self.current_image = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle('JPG Image Viewer')
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self)
        self.label.setScaledContents(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000)  # 每隔1秒检查一次

    def update_image(self):
        print("Timer triggered")  # 调试信息
        images = [f for f in os.listdir(self.image_folder) if f.lower().endswith('.png')]
        if images:
            latest_image = max(images, key=lambda f: os.path.getmtime(os.path.join(self.image_folder, f)))
            if latest_image != self.current_image:
                self.current_image = latest_image
                image_path = os.path.join(self.image_folder, latest_image)
                print(f"Loading image: {image_path}")  # 调试信息

                # 使用 QImage 加载图片
                image = QImage(image_path)
                if image.isNull():
                    print("Failed to load image.")  # 如果图片加载失败
                else:
                    pixmap = QPixmap.fromImage(image)  # 将 QImage 转换为 QPixmap
                    self.label.setPixmap(pixmap)
                    self.label.repaint()  # 强制刷新

if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_folder = 'C:\\Users\Rui Liu\Desktop\AAA\Figs'  # 替换为你的图片文件夹路径
    viewer = ImageViewer(image_folder)
    viewer.show()
    sys.exit(app.exec_())