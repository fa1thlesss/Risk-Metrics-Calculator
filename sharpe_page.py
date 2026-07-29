import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QToolButton, QSlider, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import qtawesome as qta

from widgets import add_items, make_divider, ButtonMethods
from calc import Calculation


class SharpePage(QWidget, ButtonMethods):

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

        self.description_label = QLabel("Return and benchmark parameters")
        self.description_label.setProperty("cssClass", "muted")

        risk_free_label = QLabel("Risk-free rate (annual)")
        self.risk_free_input = QLineEdit("4.5")
        self.risk_free_input.setObjectName("risk_free_input")
        self.risk_free_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        percent_label = QLabel("%")

        suffix_layout = QHBoxLayout(self.risk_free_input)
        suffix_layout.setContentsMargins(0, 0, 0, 0)
        suffix_layout.addSpacing(30)
        suffix_layout.addWidget(percent_label)
        suffix_layout.addStretch()

        self.risk_free_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.risk_free_input.setTextMargins(6, 0, 0, 0)
        self.risk_free_input.setFrame(False)

        lookback_label = QLabel("Lookback period (days)")
        self.lookback_input = QLineEdit("500")

        trading_days_label = QLabel("Trading days / year")
        self.trading_days_choice = QComboBox()
        self.trading_days_choice.addItems(["252", "365"])

        divider1 = make_divider()

        rolling_title = QLabel("Rolling window")
        rolling_title.setProperty("cssClass", "bold-label")

        window_header = QLabel("Window size (days)")
        self.window_value_label = QLabel("63")
        window_row = QHBoxLayout()
        window_row.addWidget(window_header)
        window_row.addStretch()
        window_row.addWidget(self.window_value_label)

        self.window_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_slider.setMinimum(10)
        self.window_slider.setMaximum(252)
        self.window_slider.setValue(63)
        self.window_slider.valueChanged.connect(
            lambda v: self.window_value_label.setText(str(v))
        )

        self.calculate_button = QPushButton("Calculate Sharpe ratio")
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
            risk_free_label,
            self.risk_free_input,
            lookback_label,
            self.lookback_input,
            trading_days_label,
            self.trading_days_choice,
            divider1,
            rolling_title,
            window_row,
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
        metrics = ["sharpe_ratio", "annualized_return", "annualized_volatility"]
        titles = ["Sharpe Ratio", "Annualized Return", "Annualized Volatility"]

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
            value_label.setProperty("cssClass", "metric-value-success")

            add_items(card_layout, [title_label, value_label])
            self.result_labels[metric] = value_label
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
            risk_free_annual = float(self.risk_free_input.text()) / 100
            lookback = int(self.lookback_input.text())
            trading_days = int(self.trading_days_choice.currentText())
            window = self.window_slider.value()

            self.calc = Calculation(filepath=self.current_filepath)
        except Exception as e:
            QMessageBox.warning(self, "Error loading data", str(e))
            return

        result = self.calc.sharpe_ratio(
            lookback=lookback,
            risk_free_annual=risk_free_annual,
            trading_days=trading_days,
        )
        returns = result['returns']

        self.result_labels['sharpe_ratio'].setText(f"{result['sharpe_ratio']:.2f}")
        self.result_labels['annualized_return'].setText(f"{result['annualized_return'] * 100:.1f}%")
        self.result_labels['annualized_volatility'].setText(f"{result['annualized_volatility'] * 100:.1f}%")

        self._plot_comparison(returns, window, trading_days, result['risk_free_daily'])
        self._plot_histogram(returns, risk_free_annual, trading_days)

    def _plot_comparison(self, returns, window, trading_days, risk_free_daily):
        self.compare_figure.clear()
        ax = self.compare_figure.add_subplot(111)
        ax.set_facecolor("#333333")

        rolling_sharpe = self.calc.rolling_sharpe(returns, window, risk_free_daily, trading_days)
        if len(rolling_sharpe) > 0:
            ax.plot(rolling_sharpe, color="#5B9BD5", linewidth=1.5)

        ax.tick_params(colors="#A0A0A0")

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        self.compare_figure.text(0.02, 0.97, "Rolling Sharpe ratio", color="#FFFFFF",
                                 fontweight="bold", ha="left", va="top")
        self.compare_figure.text(0.98, 0.97, f"{window}-day window",
                                 color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.compare_figure.tight_layout(rect=[0, 0, 1, 0.85])
        self.compare_canvas.draw()

    def _plot_histogram(self, returns, risk_free_annual, trading_days):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#333333")

        cumulative_portfolio = self.calc.cumulative_return(returns)
        risk_free_line = self.calc.risk_free_curve(len(returns), risk_free_annual, trading_days)
        days = np.arange(len(returns))

        ax.plot(days, cumulative_portfolio * 100, color="#5B9BD5", linewidth=1.5)
        ax.plot(days, risk_free_line * 100, color="#898787", linewidth=1.2, linestyle="--")

        ax.tick_params(colors="#A0A0A0")

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.yaxis.grid(True, color="#4A4A4A", linewidth=0.6)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        legend_handles = [
            Line2D([0], [0], color='#5B9BD5', linewidth=2),
            Line2D([0], [0], color='#898787', linewidth=1.5, linestyle='--'),
        ]
        ax.legend(legend_handles, ["Portfolio", "Risk-free"],
                  loc="upper left", frameon=False, labelcolor="#E5E5E5", fontsize=9)

        self.figure.text(0.02, 0.97, "Cumulative return", color="#FFFFFF",
                         fontweight="bold", ha="left", va="top")
        self.figure.text(0.98, 0.97, "vs. risk-free rate",
                         color="#A0A0A0", fontsize=9, ha="right", va="top")

        self.figure.tight_layout(rect=[0, 0, 1, 0.88])
        self.canvas.draw()