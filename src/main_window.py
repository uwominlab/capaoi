#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains the main window of the application.
"""

import sys
from PySide6.QtGui import QResizeEvent, QCloseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    """
    Main window of the application.
    """

    def __init__(self) -> None:
        """
        Initialize the main window.
        """
        super().__init__()

        # Set the window title
        self.setWindowTitle("PyQt5 App")

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Resize event handler.
        """
        super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Close event handler.
        """
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
