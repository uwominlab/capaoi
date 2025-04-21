import sys

# pylint: disable=no-name-in-module
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QSlider, QPushButton, QDialog


class CameraThread(QThread):
    # Signal to send the updated parameter to the main window (or any receiver)
    param_updated = pyqtSignal(float)

    def __init__(self, initial_param=0.0):
        super().__init__()
        self.param = initial_param  # The parameter that will be adjusted by sliders

    def run(self):
        while True:
            # Simulate camera processing or some algorithm running in the background
            print(f"Processing with parameter: {self.param}")
            self.sleep(1)  # Simulate processing delay

            # Optionally, emit the updated parameter value to the main thread
            self.param_updated.emit(self.param)

    def update_param(self, new_param):
        # Update the parameter in the thread
        self.param = new_param


class SettingsWidget(QDialog):
    def __init__(self, settings, camera_thread):
        super().__init__()

        self.setWindowTitle("Settings")
        self.settings = settings
        self.camera_thread = camera_thread

        # Load the parameter from QSettings (default 0.0 if not set)
        self.initial_param = self.settings.value(
            "camera/parameter", 0.0, type=float)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Label to show the current parameter value
        self.param_label = QLabel(
            f"Current Parameter: {self.initial_param}", self)

        # Slider to adjust the parameter
        self.param_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.param_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.param_slider.setTickInterval(10)
        self.param_slider.setRange(0, 100)  # Set slider range
        # Set slider to saved value (scaled)
        self.param_slider.setValue(int(self.initial_param * 100))
        self.param_slider.valueChanged.connect(self.on_slider_value_changed)

        # Slider for parameter 2
        self.param2_slider = QSlider(Qt.Orientation.Horizontal)
        self.param2_slider.setMinimum(0)
        self.param2_slider.setMaximum(100)
        self.param2_slider.setValue(50)
        self.param2_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.param2_slider.setTickInterval(10)
        self.param2_slider.valueChanged.connect(self.update_param2)

        self.param2_label = QLabel(f"Parameter 2: {self.param2_slider.value()}")

        # Add widgets to the layout
        layout.addWidget(self.param_label)
        layout.addWidget(self.param_slider)
        layout.addWidget(self.param2_label)
        layout.addWidget(self.param2_slider)

        self.setLayout(layout)

    def on_slider_value_changed(self, value):
        # When the slider value changes, update the parameter in the CameraThread
        new_param = value / 100.0  # Normalize slider value to [0, 1]
        self.camera_thread.update_param(new_param)
        print(f"Slider Value Changed: {new_param}")

        # Save the parameter to QSettings
        self.settings.setValue("camera/parameter", new_param)
        self.param_label.setText(f"Current Parameter: {new_param:.2f}")

    def update_param2(self):
        # Update the label and handle algorithm logic for param2
        self.param2_label.setText(f"Parameter 2: {self.param2_slider.value()}")
        print(f"param 2 slider Value Changed: {self.param2_slider.value()}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Camera Parameter Adjustment")

        # Load the parameter from QSettings (default 0.0 if not set)
        self.settings = QSettings("MyCompany", "CameraApp")
        self.initial_param = self.settings.value(
            "camera/parameter", 0.0, type=float)

        # Initialize the CameraThread with a loaded parameter
        self.camera_thread = CameraThread(self.initial_param)
        # Connect the signal to update the label
        self.camera_thread.param_updated.connect(self.update_label)

        self.init_ui()
        self.camera_thread.start()  # Start the camera thread

    def init_ui(self):
        # Set up the layout and widgets
        layout = QVBoxLayout()

        # Label to show the current parameter value
        self.param_label = QLabel(
            f"Current Parameter: {self.initial_param}", self)

        # Button to open the Settings widget
        self.settings_button = QPushButton("Open Settings", self)
        self.settings_button.clicked.connect(self.open_settings)

        # Add widgets to the layout
        layout.addWidget(self.param_label)
        layout.addWidget(self.settings_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_settings(self):
        # Open the SettingsWidget in a dialog
        settings_widget = SettingsWidget(self.settings, self.camera_thread)
        settings_widget.exec()

    def update_label(self, value):
        # This method is called when the camera thread sends the updated parameter
        self.param_label.setText(f"Current Parameter: {value:.2f}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
