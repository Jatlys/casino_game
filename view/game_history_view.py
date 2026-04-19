# Game History view — scrollable list of per-round results across all games.
#
# Each entry records:
#   game      — "Deck Casino", "Blackjack", or "Baccarat"
#   player    — player name
#   result    — "win" | "loss" | "draw" | "1st" | "2nd" … (game-dependent)
#   delta     — bankroll / score change as a signed integer (e.g. +120, -50)
#   detail    — short free-text note (e.g. "Natural Blackjack", "SWEEP × 2")

from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QRectF, QRect, pyqtSignal

from view.drawn_assets import AvatarWidget


# ─────────────────────────────────────────────────────────────────────────────
# Data record
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HistoryEntry:
    """One row in the game history list."""
    game:   str          # "Deck Casino" | "Blackjack" | "Baccarat"
    player: str          # player name
    result: str          # "win" | "loss" | "draw" | "1st" / "2nd" / …
    delta:  int          # score / bankroll change (signed)
    detail: str = ""     # optional free-text note


# ─────────────────────────────────────────────────────────────────────────────
# Single row widget
# ─────────────────────────────────────────────────────────────────────────────

_RESULT_COLORS = {
    "win":  ("#4caf50", "#e8f5e9"),
    "loss": ("#f44336", "#ffebee"),
    "draw": ("#9e9e9e", "#f5f5f5"),
}
_GAME_BADGE_COLORS = {
    "Deck Casino": "#1565c0",
    "Blackjack":   "#ad1457",
    "Baccarat":    "#4e342e",
}


class _HistoryRow(QWidget):
    """QPainter-drawn row for one HistoryEntry."""

    _ROW_H = 54

    def __init__(self, entry: HistoryEntry, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setFixedHeight(self._ROW_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self._ROW_H
        e = self._entry

        # Row background
        p.setBrush(QBrush(QColor("#1e1e1e")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(2, 2, w - 4, h - 4), 6, 6)

        # Left accent bar — colour by result
        accent_hex, _ = _RESULT_COLORS.get(e.result, ("#9e9e9e", "#f5f5f5"))
        p.setBrush(QBrush(QColor(accent_hex)))
        p.drawRoundedRect(QRectF(2, 2, 5, h - 4), 6, 6)

        # Game badge (top-left pill)
        badge_color = _GAME_BADGE_COLORS.get(e.game, "#546e7a")
        badge_text  = e.game[:3].upper()      # "DEC", "BLA", "BAC"
        bw, bh = 36, 16
        bx, by = 16, 6
        p.setBrush(QBrush(QColor(badge_color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(bx, by, bw, bh), 4, 4)
        p.setPen(QPen(QColor("#ffffff")))
        p.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        p.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, badge_text)

        # Player name
        p.setPen(QPen(QColor("#eeeeee")))
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(QRect(60, 4, w // 2 - 10, 22), Qt.AlignmentFlag.AlignVCenter, e.player)

        # Detail note (small, below name)
        if e.detail:
            p.setPen(QPen(QColor("#888888")))
            p.setFont(QFont("Arial", 8))
            p.drawText(QRect(60, 28, w // 2, 20), Qt.AlignmentFlag.AlignVCenter, e.detail)

        # Delta (right side, bold, coloured)
        delta_str = f"+{e.delta}" if e.delta > 0 else str(e.delta)
        delta_color = QColor("#4caf50") if e.delta > 0 else (
            QColor("#f44336") if e.delta < 0 else QColor("#9e9e9e")
        )
        p.setPen(QPen(delta_color))
        p.setFont(QFont("Arial", 13, QFont.Weight.Black))
        p.drawText(
            QRect(w // 2, 0, w // 2 - 16, h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            delta_str,
        )

        # Result label (right-aligned, small, above delta)
        result_color = QColor(accent_hex)
        p.setPen(QPen(result_color))
        p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        result_text = e.result.upper()
        p.drawText(
            QRect(w // 2, 6, w // 2 - 16, 16),
            Qt.AlignmentFlag.AlignRight,
            result_text,
        )

        # Separator line at bottom
        p.setPen(QPen(QColor("#333333"), 1))
        p.drawLine(16, h - 1, w - 16, h - 1)


# ─────────────────────────────────────────────────────────────────────────────
# Header banner (QPainter drawn)
# ─────────────────────────────────────────────────────────────────────────────

class _HeaderBanner(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(56)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#1b5e20"))
        grad.setColorAt(1.0, QColor("#0d2e0d"))
        p.fillRect(self.rect(), grad)

        p.setPen(QPen(QColor("#ffd700"), 2))
        p.drawLine(0, h - 1, w, h - 1)

        # Card suit icons in left margin
        p.setFont(QFont("Arial", 14))
        for sym, col, x in (("♠", "#ffffff", 16), ("♥", "#cc0000", 38)):
            p.setPen(QPen(QColor(col)))
            p.drawText(QRect(x, 0, 20, h), Qt.AlignmentFlag.AlignVCenter, sym)

        p.setPen(QPen(QColor("#ffd700")))
        p.setFont(QFont("Arial", 16, QFont.Weight.Black))
        p.drawText(
            QRect(0, 0, w, h),
            Qt.AlignmentFlag.AlignCenter,
            "Game History",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class GameHistoryView(QWidget):
    """Scrollable list of per-round results across all casino games.

    Usage in MainWindow::

        self._history_view = GameHistoryView()
        self.add_view(self._history_view, MainWindow.HISTORY)

        # after a round ends:
        self._history_view.add_entry(HistoryEntry(...))
    """

    back_pressed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[HistoryEntry] = []
        self._init_ui()

    # ── UI construction ────────────────────────────────────────────────

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(_HeaderBanner())

        # Back + clear buttons
        bar = QWidget()
        bar.setStyleSheet("background: #121212;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)

        back_btn = QPushButton("← Lobby")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.back_pressed)
        bar_layout.addWidget(back_btn)
        bar_layout.addStretch()

        self._count_lbl = QLabel("0 rounds played")
        self._count_lbl.setStyleSheet("color: #888888;")
        bar_layout.addWidget(self._count_lbl)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.setStyleSheet(
            "QPushButton { color: #f44336; background: #1e1e1e; "
            "border: 1px solid #444; border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { border-color: #f44336; }"
        )
        clear_btn.clicked.connect(self.clear)
        bar_layout.addWidget(clear_btn)
        root.addWidget(bar)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            "QScrollArea { background: #0d0d0d; border: none; }"
        )

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: #0d0d0d;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(12, 8, 12, 8)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        root.addWidget(self._scroll, stretch=1)

        # Empty-state label
        self._empty_lbl = QLabel("No rounds played yet.\nStart a game from the Lobby.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #555555; font-size: 14px;")
        self._list_layout.insertWidget(0, self._empty_lbl)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0d0d0d"))

    # ── Public API ─────────────────────────────────────────────────────

    def add_entry(self, entry: HistoryEntry) -> None:
        """Append a new round result and scroll to it."""
        self._entries.append(entry)
        # Hide empty-state label once we have data
        if len(self._entries) == 1:
            self._empty_lbl.hide()

        row = _HistoryRow(entry)
        # Insert before the trailing stretch (last item)
        self._list_layout.insertWidget(self._list_layout.count() - 1, row)

        self._update_count()
        # Scroll to bottom so the newest entry is visible
        QWidget.update(self._scroll)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def clear(self) -> None:
        """Remove all history entries."""
        self._entries.clear()
        # Remove all _HistoryRow children (keep empty_lbl and stretch)
        while self._list_layout.count() > 2:
            item = self._list_layout.takeAt(1)
            w = item.widget()
            if w and w is not self._empty_lbl:
                w.deleteLater()
        self._empty_lbl.show()
        self._update_count()

    def entry_count(self) -> int:
        return len(self._entries)

    # ── Internal helpers ───────────────────────────────────────────────

    def _update_count(self) -> None:
        n = len(self._entries)
        self._count_lbl.setText(f"{n} round{'s' if n != 1 else ''} played")
