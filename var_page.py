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
from widgets import add_items, make_divider, ButtonMethods
from calc import Calculation

class VarPage(QWidget, ButtonMethods):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        self.calc = None
        self.current_filepath = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._build_left_column())
        layout.addWidget(self._build_results_panel(), 1)

    def _build_left_column(self):

        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(260)
        outer_shell_layout = QVBoxLayout(left_panel)
        outer_shell_layout.setContentsMargins(16, 16, 16, 16)
        outer_shell_layout.setSpacing(10)

        button_panel = ButtonMethods._build_button_row(self)

        content_widget = QWidget()
        input_container = QVBoxLayout(content_widget)
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(12)

        self.input_icon = QLabel()
        self.input_icon.setPixmap(qta.icon('ph.sliders-light').pixmap(18, 18))
        self.input_label = QLabel("Inputs")
        self.input_label.setProperty("cssClass", "bold-label")

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(self.input_icon)
        title_row.addWidget(self.input_label)
        title_row.addStretch()

        self.description_label = QLabel("Portfolio and model parameters")
        self.description_label.setProperty("cssClass", "muted")

        portfolio_value_label = QLabel("Portfolio value")
        self.value_input_field = QLineEdit("1000000")
        self.value_input_field.setObjectName("value_input_field")

        dollar_label = QLabel("$")
        dollar_label.setProperty("cssClass", "muted")

        prefix_layout = QHBoxLayout(self.value_input_field)
        prefix_layout.setContentsMargins(8, 0, 0, 0)
        prefix_layout.addWidget(dollar_label)
        prefix_layout.addStretch()

        self.value_input_field.setTextMargins(16, 0, 0, 0)
        self.value_input_field.setFrame(False)

        confidence_level_label = QLabel("Confidence level")
        self.confidence_level_choice = QComboBox()
        self.confidence_level_choice.addItems(["90%", "95%", "99%"])
        self.confidence_level_choice.setCurrentText("99%")

        horizon_label = QLabel("Time horizon (days)")
        self.horizon_choice = QLineEdit("1")

        divider1 = make_divider()

        method_title = QLabel("Method-specific")
        method_title.setProperty("cssClass", "bold-label")

        historical_lookback_label = QLabel("Historical lookback (days)")
        self.historical_lookback_input = QLineEdit("500")

        sims_header = QLabel("MC simulations")
        self.sims_value_label = QLabel("100,000")
        simulations_layout = QHBoxLayout()
        simulations_layout.addWidget(sims_header)
        simulations_layout.addStretch()
        simulations_layout.addWidget(self.sims_value_label)

        self.simulation_slider = QSlider(Qt.Orientation.Horizontal)
        self.simulation_slider.setMinimum(10)
        self.simulation_slider.setMaximum(200)
        self.simulation_slider.setValue(100)
        self.simulation_slider.valueChanged.connect(
            lambda v: self.sims_value_label.setText(f"{v * 1000:,}")
        )

        distribution_label = QLabel("MC return distribution")
        self.distribution_choice = QComboBox()
        self.distribution_choice.addItems(["Normal", "Student's t"])

        self.calculate_button = QPushButton("Calculate all methods")
        self.calculate_button.setIcon(qta.icon('fa5s.play', color='#E5E5E5', size=10))
        self.calculate_button.clicked.connect(self.run_calculation)

        divider2 = make_divider()

        self.file_icon = QLabel()
        self.file_icon.setPixmap(qta.icon('fa5s.file-csv', color='#A0A0A0').pixmap(14, 14))
        self.loaded_label = QLabel("No file loaded")
        self.loaded_label.setStyleSheet("color: #A0A0A0; font-size: 13px;")

        loaded_row = QHBoxLayout()
        loaded_row.setSpacing(6)
        loaded_row.addWidget(self.file_icon)
        loaded_row.addWidget(self.loaded_label)
        loaded_row.addStretch()

        add_items(input_container, [
            title_row,
            self.description_label,
            portfolio_value_label,
            self.value_input_field,
            confidence_level_label,
            self.confidence_level_choice,
            horizon_label,
            self.horizon_choice,
            divider1,
            method_title,
            historical_lookback_label,
            self.historical_lookback_input,
            simulations_layout,
            self.simulation_slider,
            distribution_label,
            self.distribution_choice,
            self.calculate_button,
        ])

        input_container.addStretch()
        input_container.addWidget(divider2)
        input_container.addLayout(loaded_row)

        outer_shell_layout.addWidget(content_widget)

        left_side_wrapper = QWidget()
        left_side = QVBoxLayout(left_side_wrapper)
        left_side.addWidget(button_panel)
        left_side.addWidget(left_panel)

        return left_side_wrapper

    def _build_results_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)

        cards_row = QHBoxLayout()
        self.result_labels = {}
        methods = ["parametric", "historical", "monte_carlo_normal", "monte_carlo_student"]
        titles = ["Parametric", "Historical", "Monte Carlo (Normal)", "Monte Carlo (Student's t)"]

        for method, title in zip(methods, titles):
            card = QFrame()
            card.setFixedWidth(200)
            card.setFixedHeight(80)
            card.setProperty("cssClass", "metric-card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)

            title_label = QLabel(title)
            title_label.setProperty("cssClass", "metric-card-title")

            value_label = QLabel("—")
            value_label.setProperty("cssClass", "metric-value-danger")

            add_items(card_layout, [title_label, value_label])
            self.result_labels[method] = value_label
            cards_row.addWidget(card)

        cards_row.addStretch()

        compare_card = QFrame()
        compare_card.setObjectName("compare_card")
        compare_card_layout = QVBoxLayout(compare_card)
        compare_card_layout.setContentsMargins(12, 12, 12, 12)

        self.compare_figure = Figure(figsize=(5, 2.2))
        self.compare_figure.patch.set_facecolor("#333333")
        self.compare_canvas = FigureCanvas(self.compare_figure)
        compare_card_layout.addWidget(self.compare_canvas)

        pl_card = QFrame()
        pl_card.setObjectName("pl_card")
        pl_card_layout = QVBoxLayout(pl_card)
        pl_card_layout.setContentsMargins(12, 12, 12, 12)

        self.figure = Figure(figsize=(5, 2.2))
        self.figure.patch.set_facecolor("#333333")
        self.canvas = FigureCanvas(self.figure)
        pl_card_layout.addWidget(self.canvas)

        plots_layout = QVBoxLayout()
        plots_layout.setSpacing(12)

        plots_layout.addLayout(cards_row)
        plots_layout.addWidget(compare_card)
        plots_layout.addWidget(pl_card)

        layout.addLayout(plots_layout)

        return container

        # -----------------------------------------------------------------
        # Logic
        # -----------------------------------------------------------------

    def run_calculation(self):
        if self.current_filepath is None:
            QMessageBox.warning(self, "No file selected", "Please open a CSV file first.")
            return

        try:
            value = float(self.value_input_field.text())
            VaR = float(self.confidence_level_choice.currentText().strip('%')) / 100

            self.calc = Calculation(
                filepath=self.current_filepath,
                value=value,
                VaR=VaR,
                simulation_number=self.simulation_slider.value() * 1000,
                degrees_of_freedom=5,
                historical_lookback=int(self.historical_lookback_input.text()),
                horizon=int(self.horizon_choice.text()),
            )

        except Exception as e:
            QMessageBox.warning(self, "Error loading data", str(e))
            return

        results = self.calc.run_all()

        self.result_labels['parametric'].setText(f"-{results['parametric']:,.2f}")
        self.result_labels['historical'].setText(f"-{results['historical']:,.2f}")
        self.result_labels['monte_carlo_normal'].setText(f"-{results['monte_carlo_normal']:,.2f}")
        self.result_labels['monte_carlo_student'].setText(f"-{results['monte_carlo_student']:,.2f}")

        if self.distribution_choice.currentText() == "Normal":
            sims = results['simulations_normal']
            var_value = results['monte_carlo_normal']
        else:
            sims = results['simulations_student']
            var_value = results['monte_carlo_student']

        self._plot_comparison(results)
        self._plot_histogram(sims, var_value)

    def _plot_comparison(self, results):
        import matplotlib.ticker as mticker
        import matplotlib.patches as mpatches

        methods = ["Monte Carlo", "Parametric", "Historical"]
        values = [
            -abs(results['monte_carlo_normal']),
            -abs(results['parametric']),
            -abs(results['historical']),
        ]
        colors = ["#5B9BD5", "#6FCF97", "#F2C94C"]

        self.compare_figure.clear()
        ax = self.compare_figure.add_subplot(111)
        ax.set_facecolor("#333333")

        bars = ax.barh(methods, values, color=colors, height=0.4)
        self.compare_figure.canvas.draw()

        inv = ax.transData.inverted()
        r_x = abs(inv.transform((6, 0))[0] - inv.transform((0, 0))[0])

        for bar, color in zip(bars, colors):
            x, y = bar.get_x(), bar.get_y()
            w, h = bar.get_width(), bar.get_height()
            bar.remove()

            x_left, x_right = min(x, x + w), max(x, x + w)
            r = min(r_x, abs(w) / 2)

            rect = mpatches.Rectangle(
                (x_left + r, y), (x_right - x_left) - 2 * r, h,
                linewidth=0, facecolor=color,
            )
            left_cap = mpatches.Ellipse((x_left + r, y + h / 2), 2 * r, h,
                                        linewidth=0, facecolor=color)
            right_cap = mpatches.Ellipse((x_right - r, y + h / 2), 2 * r, h,
                                         linewidth=0, facecolor=color)
            ax.add_patch(rect)
            ax.add_patch(left_cap)
            ax.add_patch(right_cap)

        ax.set_title("")
        ax.tick_params(colors="#A0A0A0")

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.xaxis.set_major_locator(mticker.MultipleLocator(10000))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
        ax.grid(axis='x', color="#4A4A4A", linewidth=0.6)
        ax.set_axisbelow(True)

        self.compare_figure.text(0.02, 0.97, "VaR comparison across methods", color="#FFFFFF",
                                 fontweight="bold", ha="left", va="top")
        self.compare_figure.text(0.98, 0.97,
                                 f"{self.confidence_level_choice.currentText()}, {self.horizon_choice.text()} days",
                                 color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.compare_figure.tight_layout(rect=[0, 0, 1, 0.85])
        self.compare_canvas.draw()

    def _plot_histogram(self, simulations, var_value):
        import numpy as np
        import matplotlib.ticker as mticker

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#333333")

        counts, bin_edges = np.histogram(simulations, bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_width = bin_edges[1] - bin_edges[0]

        colors = ["#E57373" if c < -var_value else "#5B9BD5" for c in bin_centers]
        ax.bar(bin_centers, counts, width=bin_width, color=colors, align="center")

        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(colors="#A0A0A0", length=0)

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}"))

        ax.set_title("")

        legend_handles = [
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#5B9BD5',
                   markersize=8, linestyle=''),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#E57373',
                   markersize=8, linestyle=''),
        ]
        ax.legend(legend_handles, ["Simulated returns", "Beyond VaR"],
                  loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2,
                  frameon=False, labelcolor="#E5E5E5", fontsize=9)

        self.figure.text(0.02, 0.97, "Simulated P&L distribution", color="#FFFFFF",
                         fontweight="bold", ha="left", va="top")
        self.figure.text(0.98, 0.97, f"Monte Carlo, {len(simulations):,} paths",
                         color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.figure.tight_layout(rect=[0, 0, 1, 0.88])
        self.canvas.draw()