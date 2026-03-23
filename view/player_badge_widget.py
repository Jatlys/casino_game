# QPainter-drawn player score badge.
# Shows name, score, sweeps for every player.
# AI players additionally show a "⚙ CPU" label and a coloured difficulty pill.

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF

from model.player import Player

# Avatar circle colours — chosen deterministically from the player name
_AVATAR_PALETTE = [
    "#1565c0", "#6a1b9a", "#00695c", "#e65100",
    "#4e342e", "#37474f", "#ad1457", "#00838f",
]
_AVATAR_D = 22   # avatar diameter (px)

# Difficulty pill colours (background)
_DIFF_COLOR = {
    "easy":   QColor("#2e7d32"),   # green
    "medium": QColor("#e65100"),   # amber / orange
    "hard":   QColor("#c62828"),   # red
}
_DIFF_LABEL = {
    "easy":   "EASY",
    "medium": "MED",
    "hard":   "HARD",
}

_BADGE_H        = 34    # total widget height
_CPU_BADGE_W    = 50    # width of the "⚙ CPU" label pill
_DIFF_PILL_W    = 40    # width of the difficulty pill
_PILL_H         = 18    # shared pill height
_PAD            = 8     # horizontal padding


class PlayerBadgeWidget(QWidget):
    """QPainter-drawn badge representing one player in the score row.

    Layout (left → right):
      [padding] [⚙ CPU] [name: X pts  (Y sweeps)] ... [EASY|MED|HARD] [padding]
      The CPU badge and difficulty pill are only drawn for AI players.
      The current player's badge has a brighter background.
    """

    def __init__(self, player: Player, is_current: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self._player = player
        self._is_current = is_current
        self.setFixedHeight(_BADGE_H)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(self._compute_min_width())

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Background — brighter for the active player
        bg = QColor("#388e3c") if self._is_current else QColor("#1b5e20")
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)

        # Active player: gold left accent bar
        if self._is_current:
            painter.setBrush(QBrush(QColor("#ffd700")))
            painter.drawRoundedRect(QRectF(0, 0, 4, h), 2, 2)

        x = _PAD + (4 if self._is_current else 0)   # start after accent bar

        # Avatar circle with player initial
        x = self._draw_avatar(painter, x, h) + 6

        # CPU badge (AI only)
        if self._player.is_ai:
            x = self._draw_cpu_badge(painter, x, h) + 6

        # Right boundary — leave room for the difficulty pill if AI
        right = w - _PAD
        if self._player.is_ai:
            right = w - _DIFF_PILL_W - _PAD - 6

        # Name + score + sweeps text
        sweeps = self._player.sweeps
        sweep_str = f"  ({sweeps} sweep{'s' if sweeps != 1 else ''})" if sweeps else ""
        text = f"{self._player.name}: {self._player.total_score} pts{sweep_str}"
        text_color = QColor("#ffd700") if self._is_current else QColor("#ffffff")
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(
            QRect(x, 0, right - x, h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )

        # Difficulty pill (AI only)
        if self._player.is_ai:
            self._draw_difficulty_pill(painter, w, h)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_avatar(self, painter: QPainter, x: int, h: int) -> int:
        """Draw a circular avatar with the player's initial. Returns x after it."""
        d   = _AVATAR_D
        y   = (h - d) // 2
        idx = sum(ord(c) for c in self._player.name) % len(_AVATAR_PALETTE)
        bg  = QColor(_AVATAR_PALETTE[idx])

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawEllipse(x, y, d, d)

        initial = self._player.name[:1].upper() if self._player.name else "?"
        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(QRect(x, y, d, d), Qt.AlignmentFlag.AlignCenter, initial)
        return x + d

    def _draw_cpu_badge(self, painter: QPainter, x: int, h: int) -> int:
        """Draw the '⚙ CPU' label pill. Returns the x position after the badge."""
        pill_y = (h - _PILL_H) // 2
        painter.setBrush(QBrush(QColor("#546e7a")))   # blue-grey
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x, pill_y, _CPU_BADGE_W, _PILL_H), 4, 4)

        painter.setPen(QPen(QColor("#eceff1")))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(
            QRect(x, pill_y, _CPU_BADGE_W, _PILL_H),
            Qt.AlignmentFlag.AlignCenter,
            "⚙ CPU",
        )
        return x + _CPU_BADGE_W

    def _draw_difficulty_pill(self, painter: QPainter, w: int, h: int) -> None:
        """Draw the difficulty pill flush to the right edge."""
        diff  = self._player.difficulty
        color = _DIFF_COLOR.get(diff, QColor("#555555"))
        label = _DIFF_LABEL.get(diff, diff.upper())

        pill_x = w - _DIFF_PILL_W - _PAD
        pill_y = (h - _PILL_H) // 2

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(pill_x, pill_y, _DIFF_PILL_W, _PILL_H), 9, 9)

        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.drawText(
            QRect(pill_x, pill_y, _DIFF_PILL_W, _PILL_H),
            Qt.AlignmentFlag.AlignCenter,
            label,
        )

    # ------------------------------------------------------------------
    # Size hint
    # ------------------------------------------------------------------

    def _compute_min_width(self) -> int:
        base = _PAD * 2 + _AVATAR_D + 6 + 160   # padding + avatar + name/score text
        if self._player.is_ai:
            base += _CPU_BADGE_W + 6 + _DIFF_PILL_W + 6
        return base
