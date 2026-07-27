from PyQt6.QtWidgets import QFrame, QLayout, QFileDialog, QMessageBox
import pandas as pd

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


class PageMethods:

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