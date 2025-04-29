#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains the main window of the application.
"""

from datetime import datetime
import heapq
import time
import os
from typing import Union, Optional
import numpy as np

# pylint: disable=no-name-in-module
from PyQt6.QtCore import Qt, QTimer, QSignalBlocker
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCloseEvent, QResizeEvent
from PyQt6.QtWidgets import QComboBox, QLabel, QFrame
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QMainWindow
from PyQt6.QtWidgets import QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtWidgets import QCheckBox, QPushButton, QSpacerItem, QSizePolicy, QHeaderView
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QFileDialog

from src.camera_thread import CameraThread
from src.parameter import DefectDetectionParams
from src.relay_controller import RelayController

from src.params import ROOT_DIR
from src.params import INIT_WIDTH, INIT_HEIGHT
from src.params import ACTUATOR_RETRACTION_TIME, RELAY_1

IMAGE_RATIO: float = 0.55


# pylint: disable=too-many-instance-attributes
class MainWindow(QMainWindow):
    """
    Main window of the application.
    """

    camera_thread: CameraThread
    detection_params: DefectDetectionParams
    actuation_timestamps: list[float]
    last_actuation_time: Union[None, float] = None
    relay: RelayController

    image_label: QLabel
    time_label: QLabel
    status_label: QLabel
    status_led: QLabel
    config_combo: QComboBox
    toggle_params_checkbox: QCheckBox

    capsule_params_group: QGroupBox
    capsule_param_table: QTableWidget
    capsule_params_layout: QFormLayout

    actuator_params_group: QGroupBox
    actuator_param_table: QTableWidget
    actuator_params_layout: QFormLayout

    capsule_sample_label: QLabel

    update_config_btn: QPushButton
    config_files: list[str] = []

    start_btn: QPushButton
    pause_btn: QPushButton
    stop_btn: QPushButton

    def init_window_and_labels(self) -> None:
        """
        Setup Window and construct the labels.
        """
        # Set the window title and icon
        self.setWindowTitle("Capsule Defects Automated Optical Inspection")
        self.setWindowIcon(QIcon(f"{ROOT_DIR}\\images\\logo.svg"))
        self.setGeometry(100, 100, 800, 500)

        # Create a label for the image and one for execution status
        self.image_label = QLabel("Waiting for image...")
        self.image_label.setFixedWidth(int(INIT_WIDTH * IMAGE_RATIO))
        self.image_label.setFixedHeight(int(INIT_HEIGHT * IMAGE_RATIO))
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("Status: Starting")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_led = QLabel()
        self.status_led.setFixedSize(20, 20)
        self.status_led.setStyleSheet(
            "background-color: red; border-radius: 10px;")
        self.status_led.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def init_config_and_param_tables(self, layout: QVBoxLayout) -> None:
        """
        Initialize the left layout of the main window.
        """
        # Add a combo box to select the configuration file
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Configuration"))
        self.config_combo = QComboBox()
        self.config_combo.addItem("Please select a configuration")
        self.load_config_files()
        self.config_combo.currentIndexChanged.connect(self.load_config_param)
        config_layout.addWidget(self.config_combo)
        layout.addLayout(config_layout)

        # Add a figure display to show the example image of the capsule
        capsule_figure = QGroupBox("Capsule Sample Image")
        capsule_figure_layout = QVBoxLayout()
        self.capsule_sample_label = QLabel()
        self.capsule_sample_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capsule_figure_layout.addWidget(self.capsule_sample_label)
        capsule_figure.setLayout(capsule_figure_layout)
        layout.addWidget(capsule_figure)

        # Add a button to show all the configuration parameters
        self.toggle_params_checkbox = QCheckBox("Show parameters")
        self.toggle_params_checkbox.setChecked(False)
        self.toggle_params_checkbox.toggled.connect(
            self.toggle_params_visibility)
        layout.addWidget(self.toggle_params_checkbox)

        # Add a table to display the configuration parameters
        self.capsule_params_group = QGroupBox("Capsule Parameters")
        self.capsule_params_layout = QFormLayout(self.capsule_params_group)
        self.capsule_param_table = QTableWidget()
        self.capsule_param_table.setColumnCount(3)
        self.capsule_param_table.setHorizontalHeaderLabels(
            ["Parameter", "Lower bound", "Upper bound"])
        self.capsule_param_table.itemChanged.connect(
            self.update_defects_detection_params)
        # Enable dynamic resizing for all columns
        header: QHeaderView | None = self.capsule_param_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(
                2, QHeaderView.ResizeMode.Stretch)
        # Add the table to the layout
        self.capsule_params_layout.addWidget(self.capsule_param_table)
        layout.addWidget(self.capsule_params_group)
        self.capsule_params_group.setVisible(False)

        # Add a spacer between cpasule and actuator parameters
        layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Add a table to display the actuator parameters
        self.actuator_params_group = QGroupBox("Actuator Parameters")
        self.actuator_params_layout = QFormLayout(self.actuator_params_group)
        self.actuator_param_table = QTableWidget()
        self.actuator_param_table.setColumnCount(2)
        self.actuator_param_table.setHorizontalHeaderLabels(
            ["Parameter", "Value"])
        # Enable dynamic sizing for all columns
        header = self.actuator_param_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch)
        # Add the table to the layout
        self.actuator_params_layout.addWidget(self.actuator_param_table)
        layout.addWidget(self.actuator_params_group)
        self.actuator_params_group.setVisible(False)

    def __init__(self) -> None:
        """
        Initialize the main window.
        """
        super().__init__()
        self.init_window_and_labels()

        # Use a horizontal layout to stack the image and status labels
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Create a left panel for configuration and parameters
        left_panel = QFrame()
        left_panel.setFixedSize(500, 900)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(self.status_led)
        left_layout.addStretch()

        # Initialize the left layout of the main window
        self.init_config_and_param_tables(left_layout)
        # Add buttons to update configuration and start/pause detection
        btn_layout = QHBoxLayout()
        self.update_config_btn = QPushButton("Save Configuration")
        self.update_config_btn.clicked.connect(self.save_config)
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_detection)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_detection)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_detection)
        btn_layout.addWidget(self.update_config_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        left_panel.setLayout(left_layout)

        # Add the right panel for the image and status labels
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        status_layout = QHBoxLayout()
        self.time_label = QLabel()
        status_layout.addWidget(QLabel("Time: "))
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()

        right_layout.addLayout(status_layout)
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.status_label)
        right_layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Add the left panel, image label, and status label to the main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        self.adjustSize()

        # Connect camear thread signals to update_frame and process_actuation_timestamps methods
        self.detection_params = DefectDetectionParams()
        self.camera_thread = CameraThread(params=self.detection_params)
        self.camera_thread.frame_signal.connect(self.update_frame)
        self.camera_thread.relay_signal.connect(
            self.process_actuation_timestamps)
        self.camera_thread.camera_temperature_signal.connect(
            lambda temp: self.update_status_led("green" if temp == "Ok" else "red"))
        self.actuation_timestamps = []
        self.relay = RelayController()
        self.update_time()

    def update_frame(
        self, image: np.ndarray, count: int, timestamp: float, frame_rate: float
    ) -> None:
        """
        Update the image label with the latest frame.

        Args:
            image (np.ndarray[np.uint8]): OpenCV image array
            count (int): Total frame count
            timestamp (float): Timestamp of the frame
        """
        height, width = image.shape[:2]
        bytes_per_line = width * 3

        qimage: QImage = QImage(
            image.data, width, height, bytes_per_line,
            QImage.Format.Format_BGR888)
        pixmap: QPixmap = QPixmap.fromImage(qimage)

        # Scale the pixmap to fit the label while preserving aspect ratio
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Update the status label with frame count and timestamp
        status_text: str = \
            f"Frame: {count} | Timestamp: {timestamp:.2f} | Frame Rate: {frame_rate:.2f} fps"
        self.status_label.setText(status_text)
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def process_actuation_timestamps(self, abs_actuation_timestamps: list[float]) -> None:
        """
        This method processes a list of absolute actuation timestamps by adding them to the
        existing list of actuation timestamps, converting the list to a min-heap, and
        determining if the relay should be actuated based on the current time and the
        earliest actuation timestamp.
        If the current time is within the actuation window,
        the relay is turned on and the executed timestamp is removed from the list.
        Otherwise, the relay is turned off. The method also removes any timestamps that
        are earlier than the current time from the list of actuation timestamps.

        Args:
            timestamps (list[float]): List of actuation timestamps

        Returns:
        None

        >>> import heapq
        >>> import time
        >>> from unittest.mock import MagicMock, patch
        >>> class MockRelay:
        ...     def __init__(self):
        ...         self.state = False
        ...     def turn_on(self, relay_number):
        ...         self.state = True
        ...     def turn_off(self, relay_number):
        ...         self.state = False
        >>> class MockMainWindow:
        ...     def __init__(self):
        ...         self.camera_thread = MagicMock()
        ...         self.relay = MockRelay()
        ...         self.actuation_timestamps = []
        ...         self.last_actuation_time = None
        >>> ACTUATOR_RETRACTION_TIME = 0.1
        >>> RELAY_1 = 1
        >>> instance = MockMainWindow()
        >>> def process_actuation_timestamps_wrapper(ts: list[float]) -> None:
        ...    MainWindow.process_actuation_timestamps(instance, ts)
        >>> instance.process_actuation_timestamps = process_actuation_timestamps_wrapper

        >>> current_time = time.time()
        >>> timestamps = [current_time + 2, current_time + 10]

        >>> with patch('time.time', return_value=current_time):
        ...     instance.process_actuation_timestamps(timestamps)
        >>> instance.relay.state
        False
        >>> instance.last_actuation_time is None
        True
        >>> instance.actuation_timestamps == [current_time + 2, current_time + 10]
        True

        >>> with patch('time.time', return_value=current_time + 1.9):
        ...    instance.process_actuation_timestamps([])
        >>> instance.relay.state
        True
        >>> instance.last_actuation_time == current_time + 1.9
        True

        >>> with patch('time.time', return_value=current_time + 2.1):
        ...    instance.process_actuation_timestamps([])
        >>> instance.relay.state
        True
        >>> instance.last_actuation_time == current_time + 1.9
        True

        >>> with patch('time.time', return_value=current_time + 9.901):
        ...    instance.process_actuation_timestamps([])
        >>> instance.relay.state
        True
        >>> instance.last_actuation_time == current_time + 9.901
        True
        """
        # Add new actuation timestamps to the existing list
        # self.actuation_timestamps += abs_actuation_timestamps
        # heapq.heapify(self.actuation_timestamps)
        for timestamp in abs_actuation_timestamps:
            heapq.heappush(self.actuation_timestamps, timestamp)

        current_timestamp: float = time.time()
        # Remove expired timestamps
        while self.actuation_timestamps and self.actuation_timestamps[0] < current_timestamp:
            heapq.heappop(self.actuation_timestamps)

        # if self.actuation_timestamps:
        #     earliest_timestamp: float = self.actuation_timestamps[0]
        #     latest_timestamp: float = heapq.nlargest(
        #         1, self.actuation_timestamps)[0]
        #     latest_timestamp = max(
        #         latest_timestamp, earliest_timestamp + ACTUATOR_RETRACTION_TIME)
        #     target_timestamp: float = current_timestamp + ACTUATOR_RETRACTION_TIME
        #     if earliest_timestamp <= target_timestamp:
        #         self.relay.turn_on(relay_number=RELAY_1)
        # else:
        #     self.relay.turn_off(relay_number=RELAY_1)

        # Actuate relay based on timestamp comparison
        if self.actuation_timestamps:
            earliest_timestamp = self.actuation_timestamps[0]
            current_timestamp: float = time.time()
            target_timestamp: float = current_timestamp + ACTUATOR_RETRACTION_TIME

            # If within actuation window or still within retention time, keep the relay on
            if earliest_timestamp <= target_timestamp:
                if self.last_actuation_time is None or \
                        (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                    self.relay.turn_on(relay_number=RELAY_1)
                    self.last_actuation_time = current_timestamp
            else:
                # Not yet the time to actuate
                # Turn off only if the last actuation period has ended
                if self.last_actuation_time and \
                        (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                    self.relay.turn_off(relay_number=RELAY_1)
                    self.last_actuation_time = None
        else:
            # No more valid timestamps, turn off relay if needed
            if self.last_actuation_time and \
                    (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                self.relay.turn_off(relay_number=RELAY_1)
                self.last_actuation_time = None

    # pylint: disable=invalid-name
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """
        Resize event handler.
        """
        if self.image_label.pixmap():
            self.image_label.setPixmap(self.image_label.pixmap().scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        if a0:
            super().resizeEvent(a0)

    # pylint: disable=invalid-name
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """
        Close event handler.
        """
        # Request the camera thread to stop and wait for it to finish when closing the window
        self.camera_thread.requestInterruption()
        self.camera_thread.wait()
        # Make sure the relay is turned off and the device resources are released
        self.relay.turn_off(relay_number=RELAY_1)
        self.relay.release()
        if a0:
            a0.accept()

    def load_config_files(self) -> None:
        """
        Load configuration files from the configuration directory.
        """
        config_dir: str = f"{ROOT_DIR}\\config"
        if os.path.exists(config_dir):
            self.config_combo.clear()
            self.config_files = [
                f for f in os.listdir(config_dir) if f.endswith(".txt")]
            self.config_files = sorted(self.config_files)
            self.config_combo.addItem("Please select a configuration")
        if self.config_files:
            for file in self.config_files:
                self.config_combo.addItem(file)

    def load_config_param(self) -> None:
        """
        Load configuration parameters from the selected configuration file.
        Loads an example image of the capsule and displays it in the capsule figure zone.

        Returns:
            None
        """
        config_path: str = f"{ROOT_DIR}\\config\\{self.config_combo.currentText()}"

        if not os.path.exists(config_path):
            self.capsule_sample_label.clear()
            self.capsule_param_table.clearContents()
            self.actuator_param_table.clearContents()
            return

        self.capsule_param_table.setRowCount(0)
        self.actuator_param_table.setRowCount(0)

        capsule_row_count: int = 0
        actuator_row_count: int = 0

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        def insert_param_row(
            table: QTableWidget,
            row_count: int, param_name: str, value: str,
            min_val: Optional[str] = None, max_val: Optional[str] = None
        ) -> None:
            table.insertRow(row_count)
            table.setItem(row_count, 0, QTableWidgetItem(param_name))
            table.setItem(row_count, 1, QTableWidgetItem(
                min_val) if min_val else QTableWidgetItem(value))
            item: QTableWidgetItem | None = table.item(row_count, 1)
            if item is not None:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            table.setItem(row_count, 2, QTableWidgetItem(
                max_val) if max_val else QTableWidgetItem(value))
            item = table.item(row_count, 2)
            if item is not None:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight)

        with open(config_path, 'r', encoding='utf-8') as file:
            for _, line in enumerate(file):
                param_name, value = map(str.strip, line.strip().split(":"))

                if "Actuator" not in param_name and "actuator" not in param_name:
                    # Handling capsule parameters with min/max values
                    min_val, max_val = (
                        value.split("-") if "-" in value else ("0", value))
                    insert_param_row(
                        self.capsule_param_table,
                        capsule_row_count, param_name, value, min_val, max_val)
                    capsule_row_count += 1
                else:
                    insert_param_row(
                        self.actuator_param_table,
                        actuator_row_count, param_name, value)
                    actuator_row_count += 1

        # Set the parameter names to be uneditable
        def set_table_uneditable(table: QTableWidget, row_count: int) -> None:
            for row in range(row_count):
                item = table.item(row, 0)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        set_table_uneditable(self.capsule_param_table, 0)
        set_table_uneditable(self.actuator_param_table, 0)

        def resize_table(table: QTableWidget) -> None:
            table.resizeColumnsToContents()
            table.resizeRowsToContents()

        resize_table(self.capsule_param_table)
        resize_table(self.actuator_param_table)

        # Resize headers based on new data
        def resize_table_headers(table: QTableWidget):
            header: QHeaderView | None = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(
                    QHeaderView.ResizeMode.ResizeToContents)
                header.setStretchLastSection(True)

        resize_table_headers(self.capsule_param_table)
        resize_table_headers(self.actuator_param_table)

        # Load the example image of the capsule
        self.load_capsule_figure()

    def load_capsule_figure(self) -> None:
        """
        Load the example image of the capsule and display it in the capsule figure zone.
        """
        context: list[str] = self.config_combo.currentText().strip(
            ".txt").split("_")
        if len(context) < 2:
            return
        capsule_type = context[0] + "_" + context[1]
        capsule_figure_path: str = f"{ROOT_DIR}\\config\\{capsule_type}.png"

        if not os.path.exists(capsule_figure_path):
            self.capsule_sample_label.clear()
            QMessageBox.warning(
                self, "Missing file",
                "Corresponding capsule sample file is missing")
            return

        capsule_figure_image: QPixmap = QPixmap(capsule_figure_path)
        scaled_capsule_figure_image = capsule_figure_image.scaled(
            self.capsule_sample_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.capsule_sample_label.setPixmap(scaled_capsule_figure_image)

    def save_config(self) -> None:
        """
        Save the current configuration parameters to the selected configuration file.
        """
        config_data: list[str] = []
        item: QTableWidgetItem | None
        for row in range(self.capsule_param_table.rowCount()):
            item = self.capsule_param_table.item(row, 0)
            param_name: str = item.text() if item else ""
            item = self.capsule_param_table.item(row, 1)
            min_val: str = item.text() if item else ""
            item = self.capsule_param_table.item(row, 2)
            max_val: str = item.text() if item else ""
            config_data.append(f"{param_name}: {min_val}-{max_val}")
        for row in range(self.actuator_param_table.rowCount()):
            item = self.actuator_param_table.item(row, 0)
            param_name: str = item.text() if item else ""
            item = self.actuator_param_table.item(row, 1)
            value: str = item.text() if item else ""
            config_data.append(f"{param_name}: {value}")

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "Text Files (*.txt);;All Files (*)")

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write("\n".join(config_data))
                    file.write("\n")
                QMessageBox.information(
                    self, "Success", f"Configuration saved to {file_name}")
            # pylint: disable=broad-except
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save configuration: {str(e)}")

    def start_detection(self) -> None:
        """
        Start the detection process.
        """
        self.toggle_editable(False)
        self.camera_thread.start()
        self.update_status_led("green")

    def pause_detection(self) -> None:
        """
        Pause the detection process.
        """
        self.toggle_editable(True)
        self.relay.turn_off(relay_number=RELAY_1)
        self.camera_thread.requestInterruption()
        self.camera_thread.wait()
        self.update_status_led("red")

    def stop_detection(self) -> None:
        """
        Stop the detection process.
        """
        self.toggle_editable(True)
        self.camera_thread.requestInterruption()
        self.camera_thread.wait()
        self.update_status_led("red")
        self.image_label.clear()
        self.camera_thread.stop()
        self.status_label.setText("Status: Stopped. Waiting for image...")

    def toggle_editable(self, editable: bool) -> None:
        """
        Toggle the editable state of the configuration and parameter widgets.

        Args:
            editable (bool): Editable state

        Returns:
            None
        """
        self.config_combo.setEnabled(editable)
        self.update_config_btn.setEnabled(editable)
        self.capsule_param_table.setEnabled(editable)
        self.start_btn.setEnabled(editable)
        self.pause_btn.setEnabled(not editable)
        if not editable:
            self.capsule_param_table.setEditTriggers(
                QTableWidget.EditTrigger.NoEditTriggers)
            self.actuator_param_table.setEditTriggers(
                QTableWidget.EditTrigger.NoEditTriggers)
        else:
            self.capsule_param_table.setEditTriggers(
                QTableWidget.EditTrigger.AllEditTriggers)
            self.actuator_param_table.setEditTriggers(
                QTableWidget.EditTrigger.AllEditTriggers)

    def toggle_params_visibility(self, checked: bool) -> None:
        """Asks user for password before showing all parameters.

        Args:
            checked (bool): the status of the update config button
        """
        if checked:
            password, ok = QInputDialog.getText(
                self, "Authenication", "Password:", QLineEdit.EchoMode.Password)
            if ok:
                if password == "123456":
                    self.capsule_params_group.setVisible(True)
                    self.actuator_params_group.setVisible(True)
                    self.update_config_btn.setEnabled(True)
                else:
                    QMessageBox.warning(
                        self, "Authenication failed", "Wrong password")
                    self.toggle_params_checkbox.setChecked(False)
        else:
            self.capsule_params_group.hide()
            self.actuator_params_group.hide()
            self.update_config_btn.setEnabled(False)

    def update_time(self) -> None:
        """
        Update the time label with the current time.
        """
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        QTimer.singleShot(1000, self.update_time)

    def update_status_led(self, colour: str) -> None:
        """
        Set the status LED color.

        Args:
            color (str): Color of the LED ('red', 'green', 'yellow')

        Returns:
            None
        """
        self.status_led.setStyleSheet(
            f"background-color: {colour}; border-radius: 10px;")

    def update_defects_detection_params(self, item: QTableWidgetItem) -> None:
        """
        Updates the defect detection parameters based on the changed value in the QTableWidget.

        This method is called when a parameter value in the table is modified. It retrieves
        the parameter name and the new value, converts the value to the correct type, and 
        updates the corresponding attribute in the `DefectDetectionParams` data class. The updated
        parameters are then applied to the `camera_thread`.

        Args:
            item (QTableWidgetItem): The table item that was modified.

        Returns:
            None

        Example:
        >>> import sys
        >>> from unittest.mock import MagicMock
        >>> from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

        >>> app = QApplication(sys.argv)
        >>> params = DefectDetectionParams(
        ...     normal_length_lower=10,
        ...     normal_length_upper=50,
        ...     normal_area_lower=20,
        ...     normal_area_upper=100,
        ...     similarity_threshold=0.8,
        ...     local_defect_length=15
        ... )

        >>> class MockMainWindow:
        ...     def __init__(self):
        ...         self.detection_params = params
        ...         self.camera_thread = MagicMock()
        ...         self.capsule_param_table = QTableWidget(3, 3)
        ...         self.capsule_param_table.setItem(
        ...         0, 0, QTableWidgetItem("Contour length threshold TL (pixel)"))

        >>> def update_defects_detection_params_wrapper(item: QTableWidgetItem) -> None:
        ...    MainWindow.update_defects_detection_params(mock_window, item)
        >>> mock_window = MockMainWindow()
        >>> mock_window.update_defects_detection_params = update_defects_detection_params_wrapper
        >>> mock_window.detection_params.normal_length_lower
        10
        >>> item: QTableWidgetItem = QTableWidgetItem("30")
        >>> mock_window.capsule_param_table.setItem(0, 1, item)
        >>> item = QTableWidgetItem("60")
        >>> mock_window.capsule_param_table.setItem(0, 2, item)
        >>> mock_window.update_defects_detection_params(item)
        >>> mock_window.detection_params.normal_length_lower
        30
        >>> app.quit()
        """
        row: int = item.row()

        param_name_item: QTableWidgetItem | None = self.capsule_param_table.item(
            row, 0)
        min_value_item: QTableWidgetItem | None = self.capsule_param_table.item(
            row, 1)
        max_value_item: QTableWidgetItem | None = self.capsule_param_table.item(
            row, 2)

        if param_name_item is None or min_value_item is None or max_value_item is None:
            return

        param_name: str = param_name_item.text()
        min_value: str = min_value_item.text()
        max_value: str = max_value_item.text()

        if not '0' <= min_value <= max_value:
            QMessageBox.warning(
                self, "Invalid Input", f"Invalid boundary condition for {param_name}. \
                Lower bound should be less than or equal to upper bound."
            )
            return

        param_boundary_mapping: dict[str, dict[str, type | str]] = {
            "Contour length threshold TL (pixel)": {
                "type": int,
                "lower": "normal_length_lower",
                "upper": "normal_length_upper"
            },
            "Contour area threshold TA (pixel)": {
                "type": int,
                "lower": "normal_area_lower",
                "upper": "normal_area_upper"
            },
            "Overall contour similarity threshold TST": {
                "type": float,
                "upper": "similarity_threshold"
            },
            "Local defect length threshold TDL (pixel)": {
                "type": int,
                "upper": "local_defect_length"
            }
        }

        if param_name in param_boundary_mapping:
            mapping: dict[str, type | str] = param_boundary_mapping[param_name]
            value_type: type | str = mapping["type"]
            try:
                if min_value and "lower" in mapping and isinstance(value_type, type):
                    converted_min_value = value_type(min_value)
                    if isinstance(mapping["lower"], str) and converted_min_value is not None:
                        setattr(self.detection_params,
                                mapping["lower"], converted_min_value)

                if max_value and "upper" in mapping and isinstance(value_type, type):
                    converted_max_value = value_type(max_value)
                    if isinstance(mapping["upper"], str) and converted_max_value is not None:
                        setattr(self.detection_params,
                                mapping["upper"], converted_max_value)
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid Input", f"Invalid value for {param_name}. \
                    Expected {value_type.__name__ if isinstance(value_type, type) else value_type}."
                )
                return

            with QSignalBlocker(self.capsule_param_table):
                self.camera_thread.set_detection_params(self.detection_params)
