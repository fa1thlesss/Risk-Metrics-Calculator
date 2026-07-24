from PyQt6.QtWidgets import QFrame, QLayout

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