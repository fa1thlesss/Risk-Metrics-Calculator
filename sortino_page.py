from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel
from PyQt6.QtCore import Qt


class SortinoPage(QWidget):
    """Placeholder for the Sortino Ratio page - swap this out once the
    real inputs/results layout is built, same way VarPage is structured."""

    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window  # kept for later, once real logic is added

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("sortino_placeholder")
        card.setStyleSheet("""
            QFrame#sortino_placeholder {
                background-color: #383838;
                border-radius: 12px;
                border: 1px solid #4A4A4A;
            }
        """)
        card_layout = QVBoxLayout(card)

        label = QLabel("Sortino Ratio — coming soon")
        label.setStyleSheet("color: #A0A0A0; font-size: 16px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(label)

        layout.addWidget(card)