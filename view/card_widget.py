# Card rendering with QPainter — standard poker card proportions (1:1.4 ratio). https://www.papersizeswiki.com/standard-playing-card-size/
# Special card gold border follows project plan Section 6 special card rules.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF, pyqtSignal

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

    clicked = pyqtSignal()  # emitted when the user clicks the card

    _hint_mode: bool = False  # class-level flag; shared by all instances

    @classmethod
    def set_hint_mode(cls, enabled: bool) -> None:
        """Enable or disable the hand-value superscript badge on all cards."""
        cls._hint_mode = enabled

    def __init__(self, card: Card | None = None, face_down: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self._card = card
        self._face_down = face_down
        self._selected = False
        self.setFixedSize(CARD_W, CARD_H)

    # Public interface

    def set_card(self, card: Card | None, face_down: bool = False) -> None:
        """Update the displayed card and trigger a repaint."""
        self._card = card
        self._face_down = face_down
        self.update()

    def set_selected(self, selected: bool) -> None:
        """Highlight the card as selected and trigger a repaint."""
        self._selected = selected
        self.update()

    # Events

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()

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

        if self._selected:
            painter.setPen(QPen(QColor("#2196F3"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(1, 1, CARD_W - 2, CARD_H - 2), 6, 6)

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

        # Hint-mode badge: hand_value() as a superscript in the top-right corner
        if self._hint_mode and self._card is not None:
            self._draw_hint_badge(painter, self._card)

    def _draw_hint_badge(self, painter: QPainter, card: Card) -> None:
        """Draw a small rounded badge showing hand_value() in the top-right."""
        value = card.hand_value()
        text  = str(value)

        is_special = card.is_special()
        bg_color   = QColor("#ffd700") if is_special else QColor("#1565c0")
        fg_color   = QColor("#000000") if is_special else QColor("#ffffff")

        badge_w = 18 if value >= 10 else 14
        badge_h = 13
        badge_x = CARD_W - badge_w - 3
        badge_y = 3

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 4, 4)

        painter.setPen(QPen(fg_color))
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.drawText(
            QRect(badge_x, badge_y, badge_w, badge_h),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
