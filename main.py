"""Entry point and top-level View for the Risk Metrics app.

This module owns the ``QApplication``/``QMainWindow`` lifecycle, assembles
the three metric pages (:class:`~var_page.VarPage`,
:class:`~sharpe_page.SharpePage`, :class:`~sortino_page.SortinoPage`) into
a ``QStackedWidget``, and builds the right-hand page-navigation panel that
switches between them. It also owns the single source of truth for which
CSV is currently loaded (see :meth:`MainWindow.set_filepath`) so that
opening a file on any one page updates every page at once. All visual
styling lives in ``style.qss`` (loaded here, applied app-wide); this
module only assigns ``objectName``/``cssClass`` so those rules can target
the right widgets - it contains no ``setStyleSheet`` calls itself.
"""

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
import sys
import os
from widgets import add_items, make_divider
from var_page import VarPage
from sharpe_page import SharpePage
from sortino_page import SortinoPage

from calc import Calculation

def resource_path(relative_path):
    """Return an absolute path to a bundled resource, working both when
    running from source and when running as a PyInstaller-built .exe."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):
    """Top-level window: hosts the metric pages and the page-nav sidebar.

    Takes no constructor arguments beyond ``self`` - all three pages are
    built internally and each is handed a reference to this window (as
    ``parent_window``) so they can call back into :meth:`set_filepath`.

    Attributes
    ----------
    current_filepath:
        Path of the CSV currently loaded, shared across every page.
        ``None`` until the user opens a file. Kept in sync with each
        page's own ``current_filepath`` attribute by :meth:`set_filepath`.
    pages:
        Dict mapping a page key (``"var"``, ``"sharpe"``, ``"sortino"``)
        to its page widget instance.
    page_index:
        Dict mapping the same page keys to their integer index in
        ``self.stacked_widget``, used by :meth:`_switch_page`.
    nav_buttons:
        Dict mapping page keys to their ``QPushButton`` in the sidebar,
        used to keep the checked/unchecked state in sync with whichever
        page is currently shown.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Risk Metrics")
        self.resize(0, 800)

        self.current_filepath = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        self.page_index = {}

        var_page = VarPage(self)
        sharpe_page = SharpePage(self)
        sortino_page = SortinoPage(self)

        self.pages = {"var": var_page, "sharpe": sharpe_page, "sortino": sortino_page}

        for key, page in self.pages.items():
            self.page_index[key] = self.stacked_widget.addWidget(page)

        page_nav = self._build_page_nav()

        root_layout.addWidget(self.stacked_widget, 1)
        root_layout.addWidget(page_nav)

    def set_filepath(self, filepath):
        """Broadcast a newly opened CSV path to every page.

        Called by a page's "Open file" button (see
        ``widgets.ButtonMethods.open_file``) instead of each page setting
        its own ``current_filepath`` in isolation. Updates
        ``self.current_filepath``, every page's ``current_filepath``, and
        (where present) each page's ``loaded_label`` text - so all three
        pages always agree on which instrument's data is loaded.

        Parameters
        ----------
        filepath:
            Absolute or relative path to the newly opened CSV file.
        """
        self.current_filepath = filepath
        for page in self.pages.values():
            page.current_filepath = filepath
            if hasattr(page, "loaded_label"):
                page.loaded_label.setText(f"Loaded: {filepath.split('/')[-1]}")

    # -----------------------------------------------------------------
    # RIGHT SIDE: page navigation (VaR / Sharpe Ratio / Sortino Ratio)
    # -----------------------------------------------------------------
    def _build_page_nav(self):
        """Build the right-hand sidebar listing the three metric pages.

        Creates one checkable ``QPushButton`` per entry in ``pages``
        below, wired to :meth:`_switch_page` so clicking a button raises
        the matching widget in ``self.stacked_widget`` and unchecks the
        others (they're independent buttons, not a ``QButtonGroup``, so
        that mutual exclusivity is enforced manually in
        :meth:`_switch_page`). "Value at Risk" starts checked, matching
        the page shown first in ``self.stacked_widget``.

        Returns
        -------
        A ``QWidget`` wrapping the styled nav panel, ready to be added to
        the main window's layout.
        """
        nav_panel = QFrame()
        nav_panel.setObjectName("nav_panel")
        nav_panel.setFixedWidth(200)
        outer_shell = QWidget()
        outer_shell_layout = QVBoxLayout(outer_shell)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(6)

        nav_title = QLabel("Pages")
        nav_title.setProperty("cssClass", "section-title")
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
            btn.setProperty("cssClass", "nav")
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        self.nav_buttons["var"].setChecked(True)
        nav_layout.addStretch()
        outer_shell_layout.addWidget(nav_panel)

        return outer_shell

    def _switch_page(self, key):
        """Show the page for ``key`` and update the sidebar's checked state.

        Parameters
        ----------
        key:
            One of ``"var"``, ``"sharpe"``, ``"sortino"`` - must be a key
            present in both ``self.nav_buttons`` and ``self.page_index``.
        """
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)

        self.stacked_widget.setCurrentIndex(self.page_index[key])


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font_id = QFontDatabase.addApplicationFont(resource_path("assets/neuton.ttf"))
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 12))
    else:
        print("Warning: could not load assets/neuton.ttf, using default font.")

    with open(resource_path("style.qss"), "r") as f:
        stylesheet = f.read()

    chevron_path = resource_path("assets/chevron_white.png").replace("\\", "/")
    stylesheet = stylesheet.replace("assets/chevron_white.png", chevron_path)

    app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())