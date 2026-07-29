import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QToolButton, QSlider, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import qtawesome as qta

from widgets import add_items, make_divider, ButtonMethods
from calc import Calculation


class SortinoPage(QWidget, ButtonMethods):
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

        self.description_label = QLabel("Downside risk parameters")
        self.description_label.setProperty("cssClass", "muted")

        mar_label = QLabel("Minimum acceptable return (%)")
        self.mar_input = QLineEdit("0.5")

        lookback_label = QLabel("Lookback period (days)")
        self.lookback_input = QLineEdit("500")

        trading_days_label = QLabel("Trading days / year")
        self.trading_days_choice = QComboBox()
        self.trading_days_choice.addItems(["252", "365"])

        divider1 = make_divider()

        method_title = QLabel("Rolling window")
        method_title.setProperty("cssClass", "bold-label")

        window_header = QLabel("Window size (days)")
        self.window_value_label = QLabel("63")
        window_layout = QHBoxLayout()
        window_layout.addWidget(window_header)
        window_layout.addStretch()
        window_layout.addWidget(self.window_value_label)

        self.window_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_slider.setMinimum(10)
        self.window_slider.setMaximum(252)
        self.window_slider.setValue(63)
        self.window_slider.valueChanged.connect(
            lambda v: self.window_value_label.setText(str(v))
        )

        self.calculate_button = QPushButton("Calculate Sortino ratio")
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
            mar_label,
            self.mar_input,
            lookback_label,
            self.lookback_input,
            trading_days_label,
            self.trading_days_choice,
            divider1,
            method_title,
            window_layout,
            self.window_slider,
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
        metrics = ["sortino_ratio", "annualized_return", "downside_deviation"]
        titles = ["Sortino Ratio", "Annualized Return", "Downside Deviation"]

        for metric, title in zip(metrics, titles):
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
            self.result_labels[metric] = value_label
            cards_row.addWidget(card)

        cards_row.addStretch()

        rolling_card = QFrame()
        rolling_card.setObjectName("rolling_card")
        rolling_card_layout = QVBoxLayout(rolling_card)
        rolling_card_layout.setContentsMargins(12, 12, 12, 12)

        self.rolling_figure = Figure(figsize=(5, 2.2))
        self.rolling_figure.patch.set_facecolor("#333333")
        self.rolling_canvas = FigureCanvas(self.rolling_figure)
        rolling_card_layout.addWidget(self.rolling_canvas)

        dist_card = QFrame()
        dist_card.setObjectName("dist_card")
        dist_card_layout = QVBoxLayout(dist_card)
        dist_card_layout.setContentsMargins(12, 12, 12, 12)

        self.dist_figure = Figure(figsize=(5, 2.2))
        self.dist_figure.patch.set_facecolor("#333333")
        self.dist_canvas = FigureCanvas(self.dist_figure)
        dist_card_layout.addWidget(self.dist_canvas)

        plots_layout = QVBoxLayout()
        plots_layout.setSpacing(12)

        plots_layout.addLayout(cards_row)
        plots_layout.addWidget(rolling_card)
        plots_layout.addWidget(dist_card)

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
            mar_annual = float(self.mar_input.text().strip('%')) / 100
            lookback = int(self.lookback_input.text())
            trading_days = int(self.trading_days_choice.currentText())
            window = self.window_slider.value()

            self.calc = Calculation(filepath=self.current_filepath)
        except Exception as e:
            QMessageBox.warning(self, "Error loading data", str(e))
            return

        result = self.calc.sortino_ratio(
            lookback=lookback,
            mar_annual=mar_annual,
            trading_days=trading_days,
        )
        returns = result['returns']
        sortino = result['sortino_ratio']

        self.result_labels['sortino_ratio'].setText(f"{sortino:.2f}" if np.isfinite(sortino) else "\u221e")
        self.result_labels['annualized_return'].setText(f"{result['annualized_return'] * 100:.1f}%")
        self.result_labels['downside_deviation'].setText(
            f"{result['annualized_downside_deviation'] * 100:.1f}%"
        )

        self._plot_rolling_sortino(returns, window, trading_days, result['mar_daily'])
        self._plot_distribution(returns, result['mar_daily'])

    def _plot_rolling_sortino(self, returns, window, trading_days, mar_daily):
        self.rolling_figure.clear()
        ax = self.rolling_figure.add_subplot(111)
        ax.set_facecolor("#333333")

        rolling_sortino = self.calc.rolling_sortino(returns, window, mar_daily, trading_days)
        if len(rolling_sortino) > 0:
            ax.plot(rolling_sortino, color="#5B9BD5", linewidth=1.5)

        ax.tick_params(colors="#A0A0A0")
        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)

        self.rolling_figure.text(0.02, 0.97, "Rolling Sortino ratio", color="#FFFFFF",
                                 fontweight="bold", ha="left", va="top")
        self.rolling_figure.text(0.98, 0.97, f"{window}-day window",
                                 color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.rolling_figure.tight_layout(rect=[0, 0, 1, 0.88])
        self.rolling_canvas.draw()

    def _plot_distribution(self, returns, mar_daily):
        self.dist_figure.clear()
        ax = self.dist_figure.add_subplot(111)
        ax.set_facecolor("#333333")

        counts, bin_edges = np.histogram(returns, bins=45)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_width = bin_edges[1] - bin_edges[0]

        colors = ["#E57373" if c < mar_daily else "#5B9BD5" for c in bin_centers]
        ax.bar(bin_centers, counts, width=bin_width, color=colors, align="center")

        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(colors="#A0A0A0", length=0)

        self.dist_figure.text(0.02, 0.97, "Daily returns distribution", color="#FFFFFF",
                              fontweight="bold", ha="left", va="top")
        self.dist_figure.text(0.98, 0.97, f"vs. MAR, {len(returns):,} days",
                              color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.dist_figure.tight_layout(rect=[0, 0, 1, 0.88])
        self.dist_canvas.draw()