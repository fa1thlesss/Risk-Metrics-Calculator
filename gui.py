from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import qtawesome as qta
from PyQt6.QtCore import Qt

from main import Calculation

def add_items(layout, items):
    for item in items:
        if isinstance(item, QLayout):
            layout.addLayout(item)
        else:
            layout.addWidget(item)

def make_divider():
    divider = QFrame()
    divider.setFixedHeight(1)
    divider.setStyleSheet("background-color: #4A4A4A; border: none;")
    return divider


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        self.setGeometry(600, 200, 1400, 800)
        self.setWindowTitle('Var Calculator')
        self.setUpMainWindow()
        self.show()

    def setUpMainWindow(self):
        # Left Side
        open_button = QPushButton(' Open File', self)
        open_button.setIcon(qta.icon('fa5.folder-open'))
        open_button.setFixedWidth(120)
        refresh_button = QPushButton(' Refresh Data', self)
        refresh_button.setIcon(qta.icon('ei.refresh'))
        refresh_button.setFixedWidth(140)
        open_button.clicked.connect(self.open_file)

        inputs_icon = QLabel()
        inputs_icon.setPixmap(qta.icon('ph.sliders-light').pixmap(25, 25))
        inputs_label = QLabel('Inputs', self)
        inputs_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        description_label = QLabel('Portfolio and model parameters')
        description_label.setStyleSheet("color: #A0A0A0; margin-top: -25px")
        portfolio_value_label = QLabel('Portfolio value')
        portfolio_value_label.setStyleSheet('font-size:14px; margin-top: -25px')
        value_input_field = QLineEdit(self)
        value_input_field.setPlaceholderText('Enter the value')
        value_input_field.setStyleSheet('margin-top: -15px')
        confidence_level_label = QLabel('Confidence level')
        confidence_level_choice = QComboBox()
        confidence_level_choice.addItems(['90%', '95%', '99%'])
        horizon_label = QLabel('Time horizon')
        horizon_choice = QLineEdit(self)
        horizon_choice.setPlaceholderText('Enter the time')
        divider1 = make_divider()
        method_title = QLabel('Method-specific')
        historical_lookback_label = QLabel('Historical lookbacks (days)')
        historical_lookback_input = QLineEdit(self)
        historical_lookback_input.setPlaceholderText('Enter the lookback')
        simulations_layout = QHBoxLayout()
        simulations_label = QLabel('MC simulations')
        simulations_number = QLabel('100000')
        simulations_layout.addWidget(simulations_label)
        simulations_layout.addWidget(simulations_number)
        simulation_slider = QSlider(Qt.Orientation.Horizontal, self)
        simulation_slider.setMinimum(10000)
        simulation_slider.setMaximum(200000)
        simulation_slider.setValue(100000)
        distribution_label = QLabel('MC return distribution')
        distribution_choice = QComboBox()
        distribution_choice.addItems(['Normal', 'Student t-'])
        calculate_button = QPushButton('Calculate all methods', self)
        divider2 = make_divider()
        chosen_file = QLabel('Data/SBER.csv')

        input_panel = QFrame()
        input_panel.setObjectName("input_panel")
        input_panel.setFixedWidth(400)
        input_panel.setStyleSheet("""
            QFrame#input_panel {
                background-color: #383838;
                border-radius: 12px;
                border: 1px solid #4A4A4A;
            }
        """)

        outer_layout = QVBoxLayout(input_panel)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(8)

        content_widget = QWidget()
        content_widget.setStyleSheet('background-color: #383838;')
        input_container = QVBoxLayout(content_widget)
        input_container.setContentsMargins(32, 16, 32, 16)
        input_container.setSpacing(8)

        self.window = QHBoxLayout()

        self.left_vbox = QVBoxLayout()
        self.right_box = QVBoxLayout()

        self.button_container = QHBoxLayout()
        self.button_container.addWidget(open_button)
        self.button_container.addWidget(refresh_button)

        title_input = QHBoxLayout()
        title_input.addWidget(inputs_icon)
        title_input.addWidget(inputs_label)
        title_input.addStretch()

        add_items(input_container, [
            title_input,
            description_label,
            portfolio_value_label,
            value_input_field,
            confidence_level_label,
            confidence_level_choice,
            horizon_label,
            horizon_choice,
            divider1,
            method_title,
            historical_lookback_label,
            historical_lookback_input,
            simulations_layout,
            simulation_slider,
            distribution_label,
            distribution_choice,
            calculate_button,
            divider2,
            chosen_file,
        ])

        outer_layout.addWidget(content_widget)

        self.left_vbox.addLayout(self.button_container)
        self.left_vbox.addWidget(input_panel, alignment=Qt.AlignmentFlag.AlignLeft)

        self.window.addLayout(self.left_vbox)
        self.window.setSpacing(8)

        self.setStyleSheet("""
            background-color: #2D2D2D;
            color: #E5E5E5;
        """)


        self.setLayout(self.window)



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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())