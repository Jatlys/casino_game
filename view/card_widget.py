# Card rendering with QPainter — standard poker card proportions (1:1.4 ratio).
# Special card gold border follows project plan Section 6 special card rules.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF

from model.card import Card

# Unicode suit symbols — no image files needed
SUIT_SYMBOL = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}

SUIT_COLOR = {
    "Hearts":   QColor("#CC0000"),
    "Diamonds": QColor("#CC0000"),
    "Clubs":    QColor("#1A1A1A"),
    "Spades":   QColor("#1A1A1A"),
}

CARD_W = 70
CARD_H = 98  # 1:1.4 aspect ratio


class CardWidget(QWidget):
    """Renders a single Card (face, back, or empty slot) using QPainter.

    card=None, face_down=False  → dashed empty placeholder slot
    card=None, face_down=True   → card back (used for undealt stock)
    card set,  face_down=False  → card face with rank and suit
    card set,  face_down=True   → card back
    """

    def __init__(self, card: Card | None = None, face_down: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self._card = card
        self._face_down = face_down
        self.setFixedSize(CARD_W, CARD_H)

    # Public interface

    def set_card(self, card: Card | None, face_down: bool = False) -> None:
        """Update the displayed card and trigger a repaint."""
        self._card = card
        self._face_down = face_down
        self.update()

    # Paint event

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1, 1, CARD_W - 2, CARD_H - 2)

        if self._face_down:
            self._draw_back(painter, rect)
        elif self._card is None:
            self._draw_placeholder(painter, rect)
        else:
            self._draw_face(painter, rect)

    # Drawing helpers

    def _draw_placeholder(self, painter: QPainter, rect: QRectF) -> None:
        """Dashed outline for an empty card slot."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#888888"), 1, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(rect, 6, 6)

    def _draw_back(self, painter: QPainter, rect: QRectF) -> None:
        """Blue card back with white inner border."""
        painter.setBrush(QBrush(QColor("#1a5276")))
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawRoundedRect(rect, 6, 6)

        inner = QRectF(rect.x() + 5, rect.y() + 5,
                       rect.width() - 10, rect.height() - 10)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(inner, 4, 4)

    def _draw_face(self, painter: QPainter, rect: QRectF) -> None:
        """White card face with rank, suit symbol, and optional special border."""
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#AAAAAA"), 1))
        painter.drawRoundedRect(rect, 6, 6)

        color  = SUIT_COLOR[self._card.suit]
        symbol = SUIT_SYMBOL[self._card.suit]
        painter.setPen(QPen(color))

        # Top-left rank and suit
        font_sm = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font_sm)
        painter.drawText(QRect(4, 3, 20, 14), Qt.AlignmentFlag.AlignLeft, self._card.rank)
        painter.drawText(QRect(4, 16, 20, 14), Qt.AlignmentFlag.AlignLeft, symbol)

        # Centre suit symbol (large)
        painter.setFont(QFont("Arial", 22))
        painter.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, symbol)

        # Bottom-right rank and suit rotated 180°
        painter.save()
        painter.translate(CARD_W, CARD_H)
        painter.rotate(180)
        painter.setFont(font_sm)
        painter.drawText(QRect(4, 3, 20, 14), Qt.AlignmentFlag.AlignLeft, self._card.rank)
        painter.drawText(QRect(4, 16, 20, 14), Qt.AlignmentFlag.AlignLeft, symbol)
        painter.restore()

        # Gold border for special cards (Ace, Diamond-10, Spade-2)
        if self._card.is_special():
            painter.setPen(QPen(QColor("#FFD700"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(2, 2, CARD_W - 4, CARD_H - 4), 5, 5)
