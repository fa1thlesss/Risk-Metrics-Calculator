from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import qtawesome as qta

from main import Calculation

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        self.setGeometry(600, 200, 800, 600)
        self.setWindowTitle('Var Calculator')
        self.setUpMainWindow()
        self.show()

    def setUpMainWindow(self):
        # Left Side

        self.label1 = QLabel('1111', self)
        self.label2 = QLabel('2222', self)



        # icon + "Inputs" title on the same row

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open price data",
            "Data",
            "CSV files (*.csv);;All files (*)"
        )

        if not filepath:
            return

        self.filepath_input.setText(filepath)
        self.loaded_file_label.setText(f"Loaded: {filepath.split('/')[-1]}")

        try:
            self.calc = Calculation(filepath=filepath)
        except Exception as e:
            QMessageBox.warning(self, "Error loading file", str(e))

    # НАПИСАТЬ РЕФРЕШ


app = QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec())