# -*- coding: utf-8 -*-

""""
python control.py --log --visualize --debug
"""

import sys

# pylint: disable=no-name-in-module
# pylint: disable=unused-import
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import QCommandLineParser, QCommandLineOption
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCloseEvent, QResizeEvent
from PyQt6.QtWidgets import QComboBox, QLabel, QFrame
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QMainWindow
from PyQt6.QtWidgets import QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtWidgets import QPushButton, QSpacerItem, QSizePolicy, QHeaderView
from PyQt6.QtWidgets import QMessageBox, QApplication, QCheckBox


class CapaoiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capaoi Application")
        self.setGeometry(100, 100, 800, 600)

    def closeEvent(self, event):
        # Emit the 'destroyed' signal when the window is closed
        self.destroyed.emit()
        event.accept()


class LaunchConfigWindow(QWidget):

    capaoi_window: CapaoiWindow

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Launch Configuration")
        self.setGeometry(100, 100, 300, 250)

        # Initialize the status label
        self.status_label = QLabel("Select launch configurations:", self)

        # Create checkboxes for different launch options
        self.option1_checkbox = QCheckBox("Enable Visualization", self)
        self.option2_checkbox = QCheckBox("Enable Logging", self)
        self.option3_checkbox = QCheckBox("Enable Debug Mode", self)

        # Connect checkbox state changes to the update_status method
        self.option1_checkbox.stateChanged.connect(self.update_status)
        self.option2_checkbox.stateChanged.connect(self.update_status)
        self.option3_checkbox.stateChanged.connect(self.update_status)

        # Create the Launch button
        self.launch_button = QPushButton("Launch Application", self)
        self.launch_button.clicked.connect(self.launch_application)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.option1_checkbox)
        layout.addWidget(self.option2_checkbox)
        layout.addWidget(self.option3_checkbox)
        layout.addWidget(self.launch_button)

        self.setLayout(layout)
        # Initialize application state based on command-line arguments
        self.initialize_from_arguments()

    def initialize_from_arguments(self):
        if app.visualization_enabled:
            self.option1_checkbox.setChecked(True)
        if app.logging_enabled:
            self.option2_checkbox.setChecked(True)
        if app.debug_mode_enabled:
            self.option3_checkbox.setChecked(True)

    def update_status(self):
        # Update the status label based on the current checkbox states
        selected_options = []
        if self.option1_checkbox.isChecked():
            selected_options.append("Visualization")
        if self.option2_checkbox.isChecked():
            selected_options.append("Logging")
        if self.option3_checkbox.isChecked():
            selected_options.append("Debug Mode")

        if selected_options:
            status_text = "Selected options: " + ", ".join(selected_options)
        else:
            status_text = "No options selected."

        self.status_label.setText(status_text)

    def launch_application(self):
        # Retrieve the current state of each checkbox
        visualization_enabled = self.option1_checkbox.isChecked()
        logging_enabled = self.option2_checkbox.isChecked()
        debug_mode_enabled = self.option3_checkbox.isChecked()

        # Construct a message based on selected options
        launch_message = "Launching application with the following configurations:\n"
        if visualization_enabled:
            launch_message += "- Visualization Enabled\n"
        if logging_enabled:
            launch_message += "- Logging Enabled\n"
        if debug_mode_enabled:
            launch_message += "- Debug Mode Enabled\n"
        if not (visualization_enabled or logging_enabled or debug_mode_enabled):
            launch_message += "No configurations selected. Launching with default settings."

        # For demonstration, we'll just update the status label with the launch message
        self.status_label.setText(launch_message)

        # Create and show the Capaoi application window
        self.capaoi_window = CapaoiWindow()
        self.capaoi_window.show()

        # Disable the checkboxes after launching the application
        self.disable_checkboxes()
        self.launch_button.setEnabled(False)
        self.status_label.setText("Application launched. Checkboxes disabled.")

        # Connect the 'destroyed' signal to re-enable the checkboxes
        self.capaoi_window.destroyed.connect(self.enable_checkboxes)

    def disable_checkboxes(self):
        # Disable the checkboxes
        self.option1_checkbox.setEnabled(False)
        self.option2_checkbox.setEnabled(False)
        self.option3_checkbox.setEnabled(False)

    def enable_checkboxes(self):
        # Re-enable the checkboxes
        self.launch_button.setEnabled(True)
        self.option1_checkbox.setEnabled(True)
        self.option2_checkbox.setEnabled(True)
        self.option3_checkbox.setEnabled(True)


class MyApplication(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.setApplicationName("MyApp")
        self.setApplicationVersion("1.0")
        self.setOrganizationName("MyCompany")
        self.setOrganizationDomain("mycompany.com")

        # Set up command-line parser
        self.parser = QCommandLineParser()
        self.parser.setApplicationDescription("My PyQt6 Application")
        self.parser.addHelpOption()
        self.parser.addVersionOption()

        # Define custom command-line options
        self.visualization_option = QCommandLineOption(
            "visualize", "Enable visualization mode"
        )
        self.parser.addOption(self.visualization_option)

        self.logging_option = QCommandLineOption(
            "log", "Enable logging"
        )
        self.parser.addOption(self.logging_option)

        self.debug_option = QCommandLineOption(
            "debug", "Enable debug mode"
        )
        self.parser.addOption(self.debug_option)

        # Parse the command-line arguments
        self.parser.process(args)

        # Determine application mode based on arguments
        self.visualization_enabled = self.parser.isSet(
            self.visualization_option)
        self.logging_enabled = self.parser.isSet(self.logging_option)
        self.debug_mode_enabled = self.parser.isSet(self.debug_option)


if __name__ == "__main__":
    app = MyApplication(sys.argv)
    window = LaunchConfigWindow()
    window.show()
    sys.exit(app.exec())
