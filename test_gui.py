#!/usr/bin/env python3
"""PdfToolsXc - Debug launcher"""

import sys
import os

print("Starting PdfToolsXc...")

from PyQt6.QtWidgets import QApplication, QMessageBox

app = QApplication(sys.argv)
print(f"QApplication created, platform: {app.platformName()}")

from pdftoolsxc.gui import MainWindow

window = MainWindow()
window.setWindowTitle("PdfToolsXc - Debug Test")
window.resize(1000, 700)
window.show()

print("Window.show() called")

QMessageBox.information(None, "Debug", "If you see this, GUI is working!")

sys.exit(app.exec())
