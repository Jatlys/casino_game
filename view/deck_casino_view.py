# Deck Casino table view — visual layout only.
# Action buttons are disabled until game logic is connected in Week 3.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, pyqtSignal

from view.card_widget import CardWidget, CARD_H


class TableZoneWidget(QWidget):
    """QPainter-drawn green felt zone used for table card placement."""

    def __init__(self, zone_label: str = "", parent=None) -> None:
        super().__init__(parent)
        self._zone_label = zone_label
        self.setMinimumHeight(CARD_H + 48)

    # Paint event

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor("#1b5e20")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)

        if self._zone_label:
            painter.setPen(QPen(QColor("#ffffff60")))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(
                self.rect().adjusted(0, 6, 0, 0),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                self._zone_label,
            )


class DeckCasinoView(QWidget):
    """Visual table layout for the Deck Casino game.

    Shows the table card zone, player hand zone, sweep counter, and
    action buttons. Buttons are disabled until DeckCasinoGame is
    connected in Week 3.
    """

    back_pressed = pyqtSignal()  # emitted when the player returns to lobby

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title bar
        title_row = QHBoxLayout()
        title_lbl = QLabel("Deck Casino")
        title_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        self._sweep_label = QLabel("Sweeps: 0")
        self._sweep_label.setStyleSheet("color: #ffd700; font-weight: bold;")
        self._sweep_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        title_row.addWidget(title_lbl)
        title_row.addWidget(self._sweep_label)
        layout.addLayout(title_row)

        # Table card zone (centre of the table)
        self._table_zone = TableZoneWidget("Table Cards")
        table_row = QHBoxLayout(self._table_zone)
        table_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_row.setSpacing(10)
        table_row.setContentsMargins(12, 28, 12, 12)
        for _ in range(4):
            table_row.addWidget(CardWidget())           # empty placeholder slots
        layout.addWidget(self._table_zone, stretch=2)

        # Player hand zone (bottom of the table)
        hand_frame = QFrame()
        hand_frame.setStyleSheet("background: #2e7d32; border-radius: 10px;")
        hand_layout = QVBoxLayout(hand_frame)
        hand_layout.setContentsMargins(12, 8, 12, 8)
        hand_layout.setSpacing(6)

        self._player_name_label = QLabel("Your Hand")
        self._player_name_label.setStyleSheet("color: white; font-weight: bold;")
        hand_layout.addWidget(self._player_name_label)

        hand_row = QHBoxLayout()
        hand_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        hand_row.setSpacing(10)
        for _ in range(4):
            hand_row.addWidget(CardWidget(face_down=True))  # face-down placeholder cards
        hand_row.addStretch()
        hand_layout.addLayout(hand_row)

        layout.addWidget(hand_frame, stretch=1)

        # Action buttons
        btn_row = QHBoxLayout()
        self._back_btn  = QPushButton("← Lobby")
        self._take_btn  = QPushButton("Take Cards")
        self._place_btn = QPushButton("Place Card")
        self._take_btn.setEnabled(False)    # wired to game logic in Week 3
        self._place_btn.setEnabled(False)   # wired to game logic in Week 3
        self._back_btn.clicked.connect(lambda: self.back_pressed.emit())
        btn_row.addWidget(self._back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._take_btn)
        btn_row.addWidget(self._place_btn)
        layout.addLayout(btn_row)

    # Paint event

    def paintEvent(self, event) -> None:
        """Dark felt background for the whole game view."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a3a1a"))
