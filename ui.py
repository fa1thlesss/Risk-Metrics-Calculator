import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QToolButton, QSlider, QFileDialog,
    QMessageBox, QLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QFontDatabase
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import qtawesome as qta
import pandas as pd

from widgets import add_items, make_divider
from var_page import VarPage
from sharpe_page import SharpePage
from sortino_page import SortinoPage

from main import Calculation


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Risk Metrics")
        self.resize(1400, 800)
        self.setStyleSheet("background-color: #2D2D2D; color: #E5E5E5;")

        self.calc = None
        self.current_filepath = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        self.page_index = {}

        var_page = VarPage(self)
        sharpe_page = SharpePage(self)
        sortino_page = SortinoPage(self)

        for key, page in [("var", var_page), ("sharpe", sharpe_page), ("sortino", sortino_page)]:
            self.page_index[key] = self.stacked_widget.addWidget(page)

        page_nav = self._build_page_nav()

        root_layout.addWidget(self.stacked_widget, 1)  # stretch factor: resizes with the window
        root_layout.addWidget(page_nav)  # fixed width, always stays put

    # -----------------------------------------------------------------
    # RIGHT SIDE: page navigation (VaR / Sharpe Ratio / Sortino Ratio)
    # -----------------------------------------------------------------
    def _build_page_nav(self):
        nav_panel = QFrame()
        nav_panel.setObjectName("nav_panel")
        nav_panel.setFixedWidth(200)
        nav_panel.setStyleSheet("""
            QFrame#nav_panel {
                background-color: #383838;
                border-radius: 12px;
                border: 1px solid #4A4A4A;
            }
        """)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(6)

        nav_title = QLabel("Pages")
        nav_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #E5E5E5;")
        nav_layout.addWidget(nav_title)
        nav_layout.addWidget(make_divider())

        self.nav_buttons = {}
        pages = [
            ("var", "Value at Risk", "fa5s.chart-bar"),
            ("sharpe", "Sharpe Ratio", "fa5s.balance-scale"),
            ("sortino", "Sortino Ratio", "fa5s.arrow-down"),
        ]

        for key, label, icon_name in pages:
            btn = QPushButton(f"  {label}")
            btn.setIcon(qta.icon(icon_name, color='#E5E5E5'))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 8px;
                    color: #E5E5E5;
                }
                QPushButton:hover {
                    background: #4A4A4A;
                }
                QPushButton:checked {
                    background: #4A4A4A;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        self.nav_buttons["var"].setChecked(True)  # VaR page active by default
        nav_layout.addStretch()

        return nav_panel

    def _switch_page(self, key):
        # keep the buttons acting like a single-select group
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)

        self.stacked_widget.setCurrentIndex(self.page_index[key])


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font_id = QFontDatabase.addApplicationFont("assets/neuton.ttf")
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(font_family, 12))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())