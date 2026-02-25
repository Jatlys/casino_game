"""Quick preview of all 52 QPainter-rendered cards.
Run from the project root:  python preview_cards.py
"""

import sys

from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout,
    QLabel, QScrollArea,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from model.card import SUITS, RANKS, Card
from view.card_widget import CardWidget, CARD_W, CARD_H


class CardPreviewWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cards Preview")
        self.setStyleSheet("background: #1a3a1a;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(8)

        title = QLabel("Cards Preview")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        note = QLabel("Gold border = special card  |  columns = ranks,  rows = suits")
        note.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(note)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: #1a3a1a;")
        grid = QGridLayout(container)
        grid.setSpacing(8)
        grid.setContentsMargins(8, 8, 8, 8)

        # Column headers (ranks)
        for col, rank in enumerate(RANKS):
            lbl = QLabel(rank)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #cccccc; font-weight: bold;")
            grid.addWidget(lbl, 0, col + 1)

        # Row headers (suits) + cards
        for row, suit in enumerate(SUITS):
            lbl = QLabel(suit)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color: #cccccc; font-size: 10px; padding-right: 4px;")
            grid.addWidget(lbl, row + 1, 0)

            for col, rank in enumerate(RANKS):
                widget = CardWidget(card=Card(suit, rank), face_down=False)
                grid.addWidget(widget, row + 1, col + 1)

        scroll.setWidget(container)

        # Size the window to fit comfortably
        cols = len(RANKS) + 1
        rows = len(SUITS) + 1
        self.resize(cols * (CARD_W + 8) + 60, rows * (CARD_H + 8) + 100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardPreviewWindow()
    window.show()
    sys.exit(app.exec())
