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
import pandas as pd

from widgets import add_items, make_divider
from calc import Calculation


class SharpePage(QWidget):

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

        button_panel = QFrame()
        button_panel.setObjectName("button_panel")
        button_panel.setFixedWidth(260)
        button_panel.setStyleSheet("""
                        QFrame#button_panel {
                            background-color: #383838;
                            border-radius: 12px;
                            border: 1px solid #4A4A4A;
                        }
                    """)
        button_panel_layout = QHBoxLayout(button_panel)
        button_panel_layout.setContentsMargins(6, 0, 6, 0)
        button_panel_layout.setSpacing(4)

        self.open_button = QToolButton()
        self.open_button.setText("Open file")
        self.open_button.setIcon(qta.icon('fa5s.folder-open', color='#A0A0A0'))
        self.open_button.setIconSize(QSize(18, 18))
        self.open_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.open_button.setStyleSheet("""
                        QToolButton {
                            background: transparent;
                            border: none;
                            border-radius: 8px;
                            color: #E5E5E5;
                            padding: 6px 8px;
                        }
                    """)

        self.refresh_button = QToolButton()
        self.refresh_button.setText("Refresh data")
        self.refresh_button.setIcon(qta.icon('fa5s.sync', color='#5B9BD5'))
        self.refresh_button.setIconSize(QSize(18, 18))
        self.refresh_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.refresh_button.setStyleSheet("""
                        QToolButton {
                            background: transparent;
                            border: none;
                            border-radius: 8px;
                            color: #E5E5E5;
                            padding: 6px 8px;
                        }
                    """)

        self.open_button.clicked.connect(self.open_file)
        self.refresh_button.clicked.connect(self.refresh_data)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #4A4A4A; border: none;")

        button_panel_layout.addWidget(self.open_button)
        button_panel_layout.addWidget(divider)
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

        self.description_label = QLabel("Return and benchmark parameters")
        self.description_label.setStyleSheet("color: #A0A0A0;")

        risk_free_label = QLabel("Risk-free rate (annual)")
        self.risk_free_input = QLineEdit("4.5")
        self.risk_free_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        percent_label = QLabel("%")

        suffix_layout = QHBoxLayout(self.risk_free_input)
        suffix_layout.setContentsMargins(0, 0, 0, 0)
        suffix_layout.addSpacing(30)  # roughly where "4.5" ends, tune to taste
        suffix_layout.addWidget(percent_label)
        suffix_layout.addStretch()  # push everything else to the left, nothing pins right

        self.risk_free_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.risk_free_input.setTextMargins(6, 0, 0, 0)
        self.risk_free_input.setFrame(False)
        self.risk_free_input.setStyleSheet("""
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

        lookback_label = QLabel("Lookback period (days)")
        self.lookback_input = QLineEdit("500")
        self.lookback_input.setStyleSheet("""
                    background-color: #2D2D2D;
                    border: 1px solid #4A4A4A;
                    border-radius: 6px;
                    padding-left: 6px;
                    padding-top: 3px;
                    padding-bottom: 3px;
                    color: #E5E5E5;
                    """)

        trading_days_label = QLabel("Trading days / year")
        self.trading_days_choice = QComboBox()
        self.trading_days_choice.addItems(["252", "365"])
        self.trading_days_choice.setStyleSheet("""
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

        divider1 = make_divider()

        rolling_title = QLabel("Rolling window")
        rolling_title.setStyleSheet("font-weight: bold;")

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
            card.setObjectName(f"card_{metric}")
            card.setStyleSheet(f"""
                    QFrame#card_{metric} {{
                        background-color: #1A1A1A;
                        border-radius: 10px;
                    }}
                """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)

            title_label = QLabel(title)
            title_label.setStyleSheet("color: #A0A0A0; font-size: 16px; background-color: #1A1A1A")

            value_label = QLabel("—")
            value_label.setStyleSheet("color: #6FCF97; font-size: 20px; font-weight: bold; background-color: #1A1A1A")

            add_items(card_layout, [title_label, value_label])
            self.result_labels[metric] = value_label
            cards_row.addWidget(card)

        cards_row.addStretch()

        compare_card = QFrame()
        compare_card.setObjectName("compare_card")
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
        self.compare_figure.patch.set_facecolor("#333333")
        self.compare_canvas = FigureCanvas(self.compare_figure)
        compare_card_layout.addWidget(self.compare_canvas)

        pl_card = QFrame()
        pl_card.setObjectName("pl_card")
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
        if self.current_filepath is None:
            QMessageBox.warning(self, "No file selected", "Please open a CSV file first.")
            return

        import os
        import yfinance as yf

        ticker = os.path.splitext(os.path.basename(self.current_filepath))[0]

        try:
            existing = pd.read_csv(self.current_filepath, usecols=["Date", "Price"])
            existing["Date"] = pd.to_datetime(existing["Date"], format="mixed")
            existing = existing.sort_values("Date").reset_index(drop=True)
            last_date = existing["Date"].max()
        except Exception as e:
            QMessageBox.warning(self, "Error reading file", str(e))
            return

        start_date = last_date + pd.Timedelta(days=1)
        today = pd.Timestamp.today().normalize()

        if start_date > today:
            QMessageBox.information(self, "Refresh Data", "Already up to date.")
            return

        try:
            new_data = yf.download(ticker, start=start_date, end=today + pd.Timedelta(days=1),
                                   progress=False)
        except Exception as e:
            QMessageBox.warning(self, "Download failed",
                                f"Could not fetch data for '{ticker}':\n{e}")
            return

        if new_data.empty:
            QMessageBox.information(self, "Refresh Data", "No new data available.")
            return

        new_rows = pd.DataFrame({
            "Date": new_data.index,
            "Price": new_data["Close"].values.flatten(),
        })

        combined = pd.concat([existing, new_rows], ignore_index=True)
        combined = combined.drop_duplicates(subset="Date").sort_values("Date").reset_index(drop=True)

        to_save = combined.copy()
        to_save["Date"] = to_save["Date"].dt.strftime("%m/%d/%Y")
        to_save.to_csv(self.current_filepath, index=False)

        added = len(combined) - len(existing)
        QMessageBox.information(self, "Refresh Data",
                                f"Added {added} new row(s) for {ticker}.")

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

        full_returns = self.calc.profitability
        returns = full_returns[-lookback:] if lookback < len(full_returns) else full_returns

        mu_daily = np.mean(returns)
        sigma_daily = np.std(returns, ddof=1)
        risk_free_daily = risk_free_annual / trading_days

        annualized_return = (1 + mu_daily) ** trading_days - 1
        annualized_vol = sigma_daily * np.sqrt(trading_days)
        sharpe = (mu_daily - risk_free_daily) / sigma_daily * np.sqrt(trading_days)

        self.result_labels['sharpe_ratio'].setText(f"{sharpe:.2f}")
        self.result_labels['annualized_return'].setText(f"{annualized_return * 100:.1f}%")
        self.result_labels['annualized_volatility'].setText(f"{annualized_vol * 100:.1f}%")

        self._plot_comparison(returns, window, trading_days, risk_free_daily)
        self._plot_histogram(returns, risk_free_annual, trading_days)

    def _plot_comparison(self, returns, window, trading_days, risk_free_daily):
        self.compare_figure.clear()
        ax = self.compare_figure.add_subplot(111)
        ax.set_facecolor("#333333")

        if len(returns) > window:
            rolling_mean = np.array([
                np.mean(returns[i - window:i]) for i in range(window, len(returns))
            ])
            rolling_std = np.array([
                np.std(returns[i - window:i], ddof=1) for i in range(window, len(returns))
            ])
            rolling_sharpe = (rolling_mean - risk_free_daily) / rolling_std * np.sqrt(trading_days)
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

        cumulative_portfolio = np.cumprod(1 + returns) - 1
        days = np.arange(len(returns))
        risk_free_line = (1 + risk_free_annual) ** (days / trading_days) - 1

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