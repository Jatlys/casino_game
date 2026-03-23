# Programmatically drawn UI assets — all rendered with QPainter, no image files.
#
# Public surface
# ──────────────
#   make_window_icon(size)          → QPixmap  — 4-suit app icon
#   make_history_icon(kind, size)   → QPixmap  — "take" | "place" | "sweep"
#   AvatarWidget                    — circular player-initial badge (standalone)
#   SweepFlashOverlay               — animated full-widget sweep announcement
#   RoundResultOverlay              — styled round / game-over result dialog

from __future__ import annotations

import math

from PyQt6.QtWidgets import (
    QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDialog, QGraphicsOpacityEffect,
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPixmap, QIcon,
    QLinearGradient, QRadialGradient,
    QPainterPath,
)
from PyQt6.QtCore import (
    Qt, QRectF, QRect, QTimer, QPropertyAnimation, QEasingCurve,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Window icon  (64 × 64 by default)
# ─────────────────────────────────────────────────────────────────────────────

def make_window_icon(size: int = 64) -> QPixmap:
    """Return a QPixmap showing all four suit symbols on a dark-green background."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Dark-green rounded background
    p.setBrush(QBrush(QColor("#1b5e20")))
    p.setPen(Qt.PenStyle.NoPen)
    r = size * 0.15
    p.drawRoundedRect(QRectF(0, 0, size, size), r, r)

    # Gold border ring
    p.setPen(QPen(QColor("#ffd700"), max(2, size // 24)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), r * 0.85, r * 0.85)

    half = size // 2
    font_size = max(8, size // 5)
    p.setFont(QFont("Arial", font_size))

    # Four suits in each quadrant
    #   top-left ♠ black   top-right ♥ red
    #   bot-left ♣ black   bot-right ♦ red
    for sym, color, qx, qy in (
        ("♠", "#1a1a1a", 0,    0),
        ("♥", "#cc0000", half, 0),
        ("♣", "#1a1a1a", 0,    half),
        ("♦", "#cc0000", half, half),
    ):
        p.setPen(QPen(QColor(color)))
        p.drawText(
            QRect(qx, qy, half, half),
            Qt.AlignmentFlag.AlignCenter,
            sym,
        )

    p.end()
    return px


# ─────────────────────────────────────────────────────────────────────────────
# 2.  History row icons  — 20 × 20 QPixmaps
# ─────────────────────────────────────────────────────────────────────────────

def make_history_icon(kind: str, size: int = 20) -> QPixmap:
    """Return a small QPixmap icon for a move-history row.

    kind: "take"  — green down-arrow  (player captured table cards)
          "place" — blue  up-arrow    (player placed a card)
          "sweep" — gold 4-point star (player made a sweep)
    """
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)

    if kind == "take":
        _draw_take_icon(p, size)
    elif kind == "place":
        _draw_place_icon(p, size)
    elif kind == "sweep":
        _draw_sweep_icon(p, size)

    p.end()
    return px


def _draw_take_icon(p: QPainter, s: int) -> None:
    """Green down-arrow."""
    p.setBrush(QBrush(QColor("#4caf50")))
    shaft_w = max(3, s // 4)
    shaft_x = (s - shaft_w) // 2
    shaft_h = s * 3 // 5
    p.drawRect(shaft_x, 1, shaft_w, shaft_h)

    arrow_w = s * 3 // 4
    ax = (s - arrow_w) // 2
    path = QPainterPath()
    path.moveTo(ax,          shaft_h + 1)
    path.lineTo(s - ax,      shaft_h + 1)
    path.lineTo(s / 2,       s - 1)
    path.closeSubpath()
    p.drawPath(path)


def _draw_place_icon(p: QPainter, s: int) -> None:
    """Blue up-arrow."""
    p.setBrush(QBrush(QColor("#2196f3")))
    tip_h = s * 2 // 5
    arrow_w = s * 3 // 4
    ax = (s - arrow_w) // 2
    path = QPainterPath()
    path.moveTo(s / 2,  1)
    path.lineTo(s - ax, tip_h)
    path.lineTo(ax,     tip_h)
    path.closeSubpath()
    p.drawPath(path)

    shaft_w = max(3, s // 4)
    shaft_x = (s - shaft_w) // 2
    p.drawRect(shaft_x, tip_h, shaft_w, s - tip_h - 1)


def _draw_sweep_icon(p: QPainter, s: int) -> None:
    """Gold 4-point star."""
    p.setBrush(QBrush(QColor("#ffd700")))
    cx, cy   = s / 2, s / 2
    outer_r  = s / 2 - 1
    inner_r  = s / 5
    path = QPainterPath()
    for i in range(8):
        angle = math.radians(i * 45 - 90)
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    p.drawPath(path)


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Avatar widget  (standalone — also usable inside other widgets via paint)
# ─────────────────────────────────────────────────────────────────────────────

_AVATAR_PALETTE = [
    "#1565c0", "#6a1b9a", "#00695c", "#e65100",
    "#4e342e", "#37474f", "#ad1457", "#00838f",
]


class AvatarWidget(QWidget):
    """Circular badge showing the first letter of a player's name.

    The background colour is chosen deterministically from the name so the
    same player always gets the same colour.
    """

    def __init__(self, name: str, diameter: int = 26, parent=None) -> None:
        super().__init__(parent)
        self._initial  = name[:1].upper() if name else "?"
        idx            = sum(ord(c) for c in name) % len(_AVATAR_PALETTE)
        self._bg_color = QColor(_AVATAR_PALETTE[idx])
        self.setFixedSize(diameter, diameter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        d = min(self.width(), self.height())

        p.setBrush(QBrush(self._bg_color))
        p.setPen(QPen(QColor("#ffffff"), 1))
        p.drawEllipse(1, 1, d - 2, d - 2)

        p.setPen(QPen(QColor("#ffffff")))
        p.setFont(QFont("Arial", max(7, d // 2 - 1), QFont.Weight.Bold))
        p.drawText(QRect(0, 0, d, d), Qt.AlignmentFlag.AlignCenter, self._initial)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Sweep flash overlay
# ─────────────────────────────────────────────────────────────────────────────

class SweepFlashOverlay(QWidget):
    """Translucent full-widget overlay that announces a sweep for ~1.5 s.

    Place it as a child of the game view, then call flash(player_name)
    whenever a sweep occurs.  The overlay is mouse-transparent so it does
    not block interaction.

    Usage::

        self._sweep_flash = SweepFlashOverlay(parent=self)

        # … later, when a sweep is detected:
        self._sweep_flash.flash("Alice")
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        self._player_name = ""
        self._hint_text = ""

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self._on_anim_finished)

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._start_fade_out)

    # Public API

    def flash(self, player_name: str = "", hint_text: str = "") -> None:
        """Show the flash for the given player name.

        Args:
            player_name: Name of the player who made the sweep.
            hint_text:   Optional explanation shown below the name (hint mode).
        """
        self._player_name = player_name
        self._hint_text = hint_text
        self._fit_to_parent()
        self.show()
        self.raise_()
        self.update()

        self._anim.stop()
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(0.9)
        self._anim.start()

        self._hold_timer.start(1600 if hint_text else 1200)

    # Internal

    def _start_fade_out(self) -> None:
        self._anim.stop()
        self._anim.setDuration(480)
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if self._effect.opacity() == 0.0:
            self.hide()

    def _fit_to_parent(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())  # type: ignore[union-attr]

    def resizeEvent(self, _event) -> None:
        self._fit_to_parent()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Dark dim layer
        p.fillRect(self.rect(), QColor(0, 0, 0, 155))

        # Gold radial glow
        glow = QRadialGradient(w / 2, h / 2, min(w, h) * 0.42)
        glow.setColorAt(0.0, QColor(255, 215, 0, 160))
        glow.setColorAt(1.0, QColor(255, 215, 0, 0))
        p.fillRect(self.rect(), glow)

        # "SWEEP!" headline
        p.setPen(QPen(QColor("#ffd700")))
        p.setFont(QFont("Arial", max(36, w // 8), QFont.Weight.Black))
        p.drawText(
            QRect(0, h // 3, w, h // 4),
            Qt.AlignmentFlag.AlignCenter,
            "SWEEP!",
        )

        # Player name sub-text
        if self._player_name:
            p.setPen(QPen(QColor("#ffffff")))
            p.setFont(QFont("Arial", max(13, w // 22), QFont.Weight.Bold))
            p.drawText(
                QRect(0, h // 2, w, h // 6),
                Qt.AlignmentFlag.AlignCenter,
                self._player_name,
            )

        # Hint explanation (hint mode only)
        if self._hint_text:
            p.setPen(QPen(QColor("#ffe680")))
            p.setFont(QFont("Arial", max(9, w // 32)))
            p.drawText(
                QRect(w // 8, h * 2 // 3, w * 3 // 4, h // 5),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._hint_text,
            )


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Round / game-over result overlay
# ─────────────────────────────────────────────────────────────────────────────

class RoundResultOverlay(QDialog):
    """Dark-themed modal dialog displayed after each round or at game end.

    Shows players ranked by score with a medal indicator and a continue/
    new-game button.

    Usage::

        overlay = RoundResultOverlay(game.players, is_game_over=False, parent=self)
        overlay.exec()
    """

    def __init__(self, players: list, is_game_over: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self._players     = players
        self._is_game_over = is_game_over
        self.setModal(True)
        self.setWindowTitle("Game Over" if is_game_over else "Round Over")
        self.setStyleSheet("background: #0d1f0d;")
        self.setMinimumWidth(340)
        self._init_ui()

    def _init_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header banner ────────────────────────────────────────────────────
        header = _PaintedBanner(
            "GAME OVER" if self._is_game_over else "ROUND OVER"
        )
        outer.addWidget(header)

        # ── Score rows ───────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #122412;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 14, 20, 14)
        body_layout.setSpacing(8)

        ranked = sorted(self._players, key=lambda p: p.total_score, reverse=True)
        for rank, player in enumerate(ranked, start=1):
            body_layout.addWidget(_ScoreRow(player, rank))

        outer.addWidget(body)

        # ── Continue button ──────────────────────────────────────────────────
        btn_bar = QWidget()
        btn_bar.setStyleSheet("background: #0d1f0d;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(20, 12, 20, 16)

        btn_text = "New Game" if self._is_game_over else "Continue"
        btn = QPushButton(btn_text)
        btn.setFixedHeight(38)
        btn.setStyleSheet("""
            QPushButton {
                background: #ffd700;
                color: #1a1a1a;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 6px 28px;
                border: none;
            }
            QPushButton:hover { background: #ffe033; }
            QPushButton:pressed { background: #ccac00; }
        """)
        btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        outer.addWidget(btn_bar)


class _PaintedBanner(QWidget):
    """QPainter-drawn header for RoundResultOverlay."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self.setFixedHeight(72)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Dark-green gradient background
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#1b5e20"))
        grad.setColorAt(1.0, QColor("#0d2e0d"))
        p.fillRect(self.rect(), grad)

        # Gold bottom border line
        p.setPen(QPen(QColor("#ffd700"), 2))
        p.drawLine(0, h - 1, w, h - 1)

        # Title text
        p.setPen(QPen(QColor("#ffd700")))
        p.setFont(QFont("Arial", 20, QFont.Weight.Black))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class _ScoreRow(QWidget):
    """Single player score row inside RoundResultOverlay."""

    _MEDALS = {1: "1st", 2: "2nd", 3: "3rd"}

    def __init__(self, player, rank: int, parent=None) -> None:
        super().__init__(parent)
        self._player = player
        self._rank   = rank
        self.setFixedHeight(38)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Row background — gold tint for leader
        bg = QColor("#2a5a2a") if self._rank == 1 else QColor("#1a3a1a")
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 2, w, h - 4), 5, 5)

        text_color = QColor("#ffd700") if self._rank == 1 else QColor("#ffffff")

        # Rank label
        medal = self._MEDALS.get(self._rank, f"#{self._rank}")
        p.setPen(QPen(QColor("#aaaaaa")))
        p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        p.drawText(QRect(10, 0, 28, h), Qt.AlignmentFlag.AlignVCenter, medal)

        # Player name
        p.setPen(QPen(text_color))
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(QRect(44, 0, w // 2, h), Qt.AlignmentFlag.AlignVCenter, self._player.name)

        # Score
        pts_text = f"{self._player.total_score} pts"
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(
            QRect(w // 2, 0, w // 2 - 10, h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            pts_text,
        )

        # Sweep stars (if any)
        if self._player.sweeps:
            star_text = "★" * min(self._player.sweeps, 5)
            p.setPen(QPen(QColor("#ffd700")))
            p.setFont(QFont("Arial", 7))
            p.drawText(
                QRect(0, 0, w - 8, h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                star_text,
            )


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Point toast overlay  — compact non-blocking banner for notable captures
# ─────────────────────────────────────────────────────────────────────────────

class PointToastOverlay(QWidget):
    """Small animated banner that announces a notable card capture.

    Appears near the top of the parent widget, fades out automatically.
    Mouse-transparent so it never blocks interaction.

    Usage::

        self._point_toast = PointToastOverlay(parent=self)

        # … when a notable capture occurs:
        self._point_toast.show_event(
            title="Alice captured an Ace (+1 pt)",
            subtitle="Each Ace earns 1 point at round end.",   # hint mode only
            accent="#4caf50",
        )
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        self._title    = ""
        self._subtitle = ""
        self._accent   = QColor("#ffd700")

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self._on_anim_finished)

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._start_fade_out)

    # Public API

    def show_event(self, title: str, subtitle: str = "",
                   accent: str = "#ffd700") -> None:
        """Show the toast with a title line and optional hint subtitle."""
        self._title    = title
        self._subtitle = subtitle
        self._accent   = QColor(accent)
        self._fit_to_parent()
        self.update()
        self.show()
        self.raise_()

        self._anim.stop()
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

        hold = 2800 if subtitle else 1800
        self._hold_timer.start(hold)

    # Internal

    def _start_fade_out(self) -> None:
        self._anim.stop()
        self._anim.setDuration(500)
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if self._effect.opacity() == 0.0:
            self.hide()

    def _fit_to_parent(self) -> None:
        if self.parent():
            par = self.parent()
            height = 64 if self._subtitle else 40
            width  = min(par.width() - 40, 500)
            x      = (par.width() - width) // 2
            y      = 72
            self.setGeometry(x, y, width, height)

    def resizeEvent(self, _event) -> None:
        self._fit_to_parent()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Dark semi-transparent background
        p.setBrush(QBrush(QColor(10, 25, 10, 220)))
        p.setPen(QPen(self._accent, 2))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)

        # Left accent stripe
        p.setBrush(QBrush(self._accent))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(1, 1, 5, h - 2), 8, 8)

        # Title line
        p.setPen(QPen(self._accent))
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_rect = QRect(14, 4, w - 18, 28)
        p.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter, self._title)

        # Hint subtitle
        if self._subtitle:
            p.setPen(QPen(QColor("#bbbbbb")))
            p.setFont(QFont("Arial", 8))
            hint_rect = QRect(14, 30, w - 18, 30)
            p.drawText(
                hint_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                self._subtitle,
            )
