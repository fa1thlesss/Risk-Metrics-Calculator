import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSlider, QFileDialog,
    QMessageBox, QLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import qtawesome as qta

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



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VaR Calculator")
        self.resize(1400, 800)
        self.setStyleSheet("background-color: #2D2D2D; color: #E5E5E5;")

        self.calc = None
        self.current_filepath = "Data/SBER.csv"

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout(central_widget)

        left_column = self._build_left_column()
        results_panel = self._build_results_panel()

        root_layout.addWidget(left_column)
        root_layout.addWidget(results_panel, 1)


    def _build_left_column(self):

        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(260)
        left_panel.setStyleSheet("""
            QFrame#left_panel {
                background-color: #333333;
                border-radius: 12px;
                border: 1px solid #4A4A4A;
            }
        """)
        outer_shell_layout = QVBoxLayout(left_panel)
        outer_shell_layout.setContentsMargins(16, 16, 16, 16)
        outer_shell_layout.setSpacing(10)

        self.open_button = QPushButton(" Open File")
        self.open_button.setIcon(qta.icon('fa5s.folder-open', color='#E5E5E5'))
        self.refresh_button = QPushButton(" Refresh Data")
        self.refresh_button.setIcon(qta.icon('fa5s.sync', color='#E5E5E5'))
        self.open_button.clicked.connect(self.open_file)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.open_button.setStyleSheet("""
                background-color: #454545;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding-top: 8px;
                padding-bottom: 8px;
                padding-left: 8px;
                padding-right:8px;
                color: #E5E5E5;
                """)
        self.refresh_button.setStyleSheet("""
                        background-color: #454545;
                        border: 1px solid #4A4A4A;
                        border-radius: 6px;
                        padding-top: 8px;
                        padding-bottom: 8px;
                        padding-left: 8px;
                        padding-right: 8px;
                        color: #E5E5E5;
                        """)

        button_panel = QFrame()
        button_panel.setObjectName("button_panel")
        button_panel.setFixedWidth(260)
        button_panel.setStyleSheet("""
                    QFrame#button_panel {
                        background-color: #383838;
                        border-radius: 10px;
                        border: 1px solid #4A4A4A;
                    }
                """)

        button_panel_layout = QHBoxLayout(button_panel)
        button_panel_layout.setContentsMargins(16, 8, 16, 8)
        button_panel_layout.setSpacing(10)

        button_panel_layout.addWidget(self.open_button)
        button_panel_layout.addWidget(self.refresh_button)

        content_widget = QWidget()
        content_widget.setStyleSheet('background-color: #333333;')
        input_container = QVBoxLayout(content_widget)
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(12)

        self.input_icon = QLabel()
        self.input_icon.setPixmap(qta.icon('ph.sliders-light').pixmap(18, 18))
        self.input_label = QLabel("Inputs")
        self.input_label.setStyleSheet("font-weight: bold;")

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(self.input_icon)
        title_row.addWidget(self.input_label)
        title_row.addStretch()

        self.description_label = QLabel("Portfolio and model parameters")
        self.description_label.setStyleSheet("color: #A0A0A0;")

        portfolio_value_label = QLabel("Portfolio value")
        self.value_input_field = QLineEdit("1000000")

        dollar_label = QLabel("$")
        dollar_label.setStyleSheet("color: #A0A0A0;")

        prefix_layout = QHBoxLayout(self.value_input_field)
        prefix_layout.setContentsMargins(8, 0, 0, 0)
        prefix_layout.addWidget(dollar_label)
        prefix_layout.addStretch()

        self.value_input_field.setTextMargins(16, 0, 0, 0)
        self.value_input_field.setFrame(False)
        self.value_input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding-left: 0px;
                padding-top: 3px;
                padding-bottom: 3px;
                color: #E5E5E5;
            }
            QLineEdit:focus {
                border: 1px solid #4A4A4A;
            }
        """)

        confidence_level_label = QLabel("Confidence level")
        self.confidence_level_choice = QComboBox()
        self.confidence_level_choice.addItems(["90%", "95%", "99%"])
        self.confidence_level_choice.setCurrentText("99%")
        self.confidence_level_choice.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
            border-radius: 6px;
            padding: 4px 8px;
            color: #E5E5E5;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(assets/chevron_white.png);
                width: 10px;
                height: 10px;
            }
            """)

        horizon_label = QLabel("Time horizon (days)")
        self.horizon_choice = QLineEdit("10")
        self.horizon_choice.setStyleSheet("""
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding-left: 6px;
                padding-top: 3px;
                padding-bottom: 3px;
                color: #E5E5E5;
                """)

        divider1 = make_divider()

        method_title = QLabel("Method-specific")
        method_title.setStyleSheet("font-weight: bold;")

        historical_lookback_label = QLabel("Historical lookback (days)")
        self.historical_lookback_input = QLineEdit("500")
        self.historical_lookback_input.setStyleSheet("""
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding-left: 6px;
                padding-top: 3px;
                padding-bottom: 3px;
                color: #E5E5E5;
                """)

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
            lambda v: self.sims_value_label.setText(f"{v*1000:,}")
        )

        distribution_label = QLabel("MC return distribution")
        self.distribution_choice = QComboBox()
        self.distribution_choice.addItems(["Normal", "Student's t"])
        self.distribution_choice.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
            border-radius: 6px;
            padding: 4px 8px;
            color: #E5E5E5;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(assets/chevron_white.png);
                width: 10px;
                height: 10px;
            }
            """)

        self.calculate_button = QPushButton("Calculate all methods")
        self.calculate_button.setIcon(qta.icon('fa5s.play', color='#E5E5E5', size=10))
        self.calculate_button.setStyleSheet("""
                background-color: #454545;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding-top: 8px;
                padding-bottom: 8px;
                color: #E5E5E5;
                font-weight: bold;
                margin-top: 10px
                """)
        self.calculate_button.clicked.connect(self.run_calculation)

        divider2 = make_divider()

        self.file_icon = QLabel()
        self.file_icon.setPixmap(qta.icon('fa5s.file-csv', color='#A0A0A0').pixmap(14, 14))
        self.loaded_label = QLabel(f"Loaded: {self.current_filepath.split('/')[-1]}")
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
            card.setObjectName(f"card_{method}")
            card.setStyleSheet(f"""
                QFrame#card_{method} {{
                    background-color: #1A1A1A;
                    border-radius: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)

            title_label = QLabel(title)
            title_label.setStyleSheet("color: #A0A0A0; font-size: 16px; background-color: #1A1A1A")

            value_label = QLabel("—")
            value_label.setStyleSheet("color: #E57373; font-size: 20px; font-weight: bold; background-color: #1A1A1A")

            add_items(card_layout, [title_label, value_label])
            self.result_labels[method] = value_label
            cards_row.addWidget(card)

        cards_row.addStretch()

        compare_card = QFrame()
        compare_card.setObjectName("compare_card")
        compare_card.setFixedWidth(840)
        compare_card.setStyleSheet("""
                    QFrame#compare_card {
                        background-color: #333333;
                        border-radius: 10px;
                        border: 1px solid #4A4A4A;
                    }
                """)
        compare_card_layout = QVBoxLayout(compare_card)
        compare_card_layout.setContentsMargins(12, 12, 12, 12)

        self.compare_figure = Figure(figsize=(5, 2.2))
        self.compare_figure.patch.set_facecolor("#333333")  # matches the card, not the window
        self.compare_canvas = FigureCanvas(self.compare_figure)
        compare_card_layout.addWidget(self.compare_canvas)

        pl_card = QFrame()
        pl_card.setObjectName("pl_card")
        pl_card.setFixedWidth(840)
        pl_card.setStyleSheet("""
                    QFrame#pl_card {
                        background-color: #333333;
                        border-radius: 10px;
                        border: 1px solid #4A4A4A;
                    }
                """)
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
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open price data", "Data", "CSV files (*.csv);;All files (*)"
        )
        if not filepath:
            return

        self.current_filepath = filepath
        self.loaded_label.setText(f"Loaded: {filepath.split('/')[-1]}")

    def refresh_data(self):
        # TODO: pull latest prices via yfinance / apimoex and overwrite the CSV
        QMessageBox.information(self, "Refresh Data", "Not implemented yet.")

    def run_calculation(self):
        try:
            value = float(self.value_input_field.text())
            VaR = float(self.confidence_level_choice.currentText().strip('%')) / 100

            self.calc = Calculation(
                filepath=self.current_filepath,
                value=value,
                VaR=VaR,
                simulation_number=self.simulation_slider.value() * 1000,
                degrees_of_freedom=5,  # not yet exposed as an input
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
        self.compare_figure.canvas.draw()  # finalize transforms before converting px -> data units

        # fixed 6px corner radius, converted to data-x-units so it stays
        # visually consistent regardless of how large the value range is
        inv = ax.transData.inverted()
        r_x = abs(inv.transform((6, 0))[0] - inv.transform((0, 0))[0])

        for bar, color in zip(bars, colors):
            x, y = bar.get_x(), bar.get_y()
            w, h = bar.get_width(), bar.get_height()
            bar.remove()  # drop the original square-cornered rectangle

            x_left, x_right = min(x, x + w), max(x, x + w)
            r = min(r_x, abs(w) / 2)  # never let the cap exceed half the bar's width

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

        ax.xaxis.set_major_locator(mticker.MultipleLocator(2000))
        ax.grid(axis='x', color="#4A4A4A", linewidth=0.6)
        ax.set_axisbelow(True)  # keeps gridlines behind the bars

        self.compare_figure.text(0.02, 0.97, "VaR comparison across methods", color="#FFFFFF",
                         fontweight="bold", ha="left", va="top", fontfamily=font_family)
        self.compare_figure.text(0.98, 0.97, f"{self.confidence_level_choice.currentText()}, {self.horizon_choice.text()} days",
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

        # red for the loss tail beyond the VaR threshold, blue otherwise
        colors = ["#E57373" if c < -var_value else "#5B9BD5" for c in bin_centers]
        ax.bar(bin_centers, counts, width=bin_width, color=colors, align="center")

        # horizontal gridlines only
        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(colors="#A0A0A0", length=0)

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}"))

        ax.set_title("")  # title is drawn manually below instead

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
                         fontweight="bold", ha="left", va="top", fontfamily=font_family)
        self.figure.text(0.98, 0.97, f"Monte Carlo, {len(simulations):,} paths",
                         color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.figure.tight_layout(rect=[0, 0, 1, 0.88])
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font_id = QFontDatabase.addApplicationFont("assets/neuton.ttf")
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(font_family, 12))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())