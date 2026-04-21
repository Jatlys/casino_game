# Tutorial overlay for Deck Casino — step-by-step guided introduction.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QSize

# ---------------------------------------------------------------------------
# Tutorial step content
# ---------------------------------------------------------------------------

_STEPS = [
    (
        "Welcome to Deck Casino!",
        "Your goal is to reach <b>16 points</b> before your opponents. "
        "This short tutorial will walk you through everything you need to win."
    ),
    (
        "Reading the Screen",
        "The <b>Table Cards</b> zone (centre) holds cards shared by all players. "
        "Your <b>Hand</b> (bottom green zone) holds your private cards. "
        "The <b>Stock</b> counter (top-right) shows how many cards remain to be dealt."
    ),
    (
        "Special Cards — Gold Borders",
        "Three cards have boosted hand values:<br>"
        "&nbsp;&nbsp;&bull; <b>Ace</b> &rarr; plays as <b>14</b> (sits on table as 1)<br>"
        "&nbsp;&nbsp;&bull; <b>Diamond 10</b> &rarr; plays as <b>16</b> (table value 10)<br>"
        "&nbsp;&nbsp;&bull; <b>Spade 2</b> &rarr; plays as <b>15</b> (table value 2)<br>"
        "They have a <span style='color:#FFD700;'><b>gold border</b></span> — prioritise collecting them!"
    ),
    (
        "Taking Cards",
        "Click a card in <b>Your Hand</b> to select it (blue glow). "
        "Then click table cards whose values <b>sum to your hand card's value</b>. "
        "Press <b>Take Cards</b> to collect them into your score pile."
    ),
    (
        "Multi-Group Takes",
        "You can take <em>multiple groups at once</em> as long as every table card "
        "you select belongs to a valid group. "
        "Example: Ace (value 14) can take a 7+7 <em>and</em> a separate 6+8 in one move "
        "— just select all four table cards and press Take."
    ),
    (
        "Placing a Card",
        "If no table cards match your hand card's value, press <b>Place Card</b> "
        "to put it face-up on the table. Other players may take it later &mdash; "
        "so place low-value cards when possible to avoid helping opponents."
    ),
    (
        "Sweeps — Bonus Points!",
        "If your take clears <em>every</em> card from the table, you earn a "
        "<b>Sweep</b> (1 bonus point). The table resets empty for the next player. "
        "Chaining sweeps is one of the fastest paths to 16 points!"
    ),
    (
        "End-of-Round Scoring",
        "At round end, points are awarded:<br>"
        "&nbsp;&nbsp;&bull; <b>Most cards collected</b> &rarr; 1 pt (no award on tie)<br>"
        "&nbsp;&nbsp;&bull; <b>Most Spades collected</b> &rarr; 2 pts (no award on tie)<br>"
        "&nbsp;&nbsp;&bull; Each <b>Ace</b> collected &rarr; 1 pt<br>"
        "&nbsp;&nbsp;&bull; <b>Diamond 10</b> &rarr; 2 pts &nbsp;|&nbsp; "
        "<b>Spade 2</b> &rarr; 1 pt<br>"
        "&nbsp;&nbsp;&bull; Each <b>Sweep</b> &rarr; 1 pt"
    ),
    (
        "You're Ready to Play!",
        "Quick strategy recap:<br>"
        "&nbsp;&nbsp;&bull; Hunt <b>sweeps</b> — they are reliable free points<br>"
        "&nbsp;&nbsp;&bull; Chase <b>Diamond 10</b> (2 pts!) and Aces early<br>"
        "&nbsp;&nbsp;&bull; Keep track of Spades — 2 pts for the leader<br>"
        "&nbsp;&nbsp;&bull; Place low cards; never gift the Diamond 10<br><br>"
        "Press <b>Finish</b> to start playing. "
        "Use <b>How to Play</b> any time for the full rules reference."
    ),
]


# ---------------------------------------------------------------------------
# Step-progress dots indicator
# ---------------------------------------------------------------------------

class _StepDots(QWidget):
    """Draws N small circles; completed steps are grey, the current step is
    gold, and upcoming steps are hollow (outline only)."""

    _DIAMETER = 12
    _GAP      = 8

    def __init__(self, total: int, parent=None) -> None:
        super().__init__(parent)
        self._total   = total
        self._current = 0   # 0-based index of active step
        w = total * self._DIAMETER + (total - 1) * self._GAP
        self.setFixedSize(QSize(w, self._DIAMETER))

    def set_step(self, step: int) -> None:
        """Update the active step (0-based) and repaint."""
        self._current = step
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the step-progress dots for the tutorial overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        d   = self._DIAMETER
        gap = self._GAP

        for i in range(self._total):
            x = i * (d + gap)
            if i < self._current:
                # Completed — filled grey
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#888888")))
            elif i == self._current:
                # Current — filled gold
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#ffd700")))
            else:
                # Upcoming — hollow gold outline
                painter.setPen(QPen(QColor("#ffd700"), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(x, 0, d, d)


# ---------------------------------------------------------------------------
# TutorialOverlay widget
# ---------------------------------------------------------------------------

class TutorialOverlay(QWidget):
    """Floating tutorial panel embedded in DeckCasinoView.

    Displays _STEPS one at a time.  Emits tutorial_finished when the user
    presses Finish or Skip Tutorial.
    """

    tutorial_finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._step = 0
        self._init_ui()
        self._show_step()
        self.hide()   # hidden until start_tutorial() is called

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._panel = QFrame()
        self._panel.setStyleSheet(
            "QFrame {"
            "  background: #0d2a0d;"
            "  border: 2px solid #ffd700;"
            "  border-radius: 10px;"
            "}"
        )

        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(20, 12, 20, 12)
        panel_layout.setSpacing(6)

        # Step progress dots
        dots_row = QHBoxLayout()
        self._dots = _StepDots(len(_STEPS))
        dots_row.addWidget(self._dots)
        dots_row.addStretch()
        panel_layout.addLayout(dots_row)

        # Title
        self._title_lbl = QLabel()
        self._title_lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet("color: white; border: none;")
        self._title_lbl.setWordWrap(True)
        panel_layout.addWidget(self._title_lbl)

        # Body (rich text)
        self._body_lbl = QLabel()
        self._body_lbl.setStyleSheet(
            "color: #dddddd; font-size: 12px; border: none;"
        )
        self._body_lbl.setWordWrap(True)
        self._body_lbl.setTextFormat(Qt.TextFormat.RichText)
        panel_layout.addWidget(self._body_lbl)

        # Buttons
        btn_row = QHBoxLayout()

        self._skip_btn = QPushButton("Skip Tutorial")
        self._skip_btn.setStyleSheet(
            "QPushButton {"
            "  color: #aaaaaa; background: transparent;"
            "  border: 1px solid #555555; border-radius: 4px;"
            "  padding: 4px 10px;"
            "}"
            "QPushButton:hover { color: white; border-color: #aaaaaa; }"
        )
        self._skip_btn.clicked.connect(self._on_skip)

        _nav_style = (
            "QPushButton {"
            "  background: #ffd700; color: black; font-weight: bold;"
            "  border: none; border-radius: 4px; padding: 4px 18px;"
            "}"
            "QPushButton:hover { background: #ffe033; }"
            "QPushButton:disabled {"
            "  background: #555533; color: #888866;"
            "}"
        )

        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.setStyleSheet(_nav_style)
        self._prev_btn.clicked.connect(self._on_prev)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setStyleSheet(_nav_style)
        self._next_btn.clicked.connect(self._on_next)

        btn_row.addWidget(self._skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._prev_btn)
        btn_row.addWidget(self._next_btn)
        panel_layout.addLayout(btn_row)

        outer.addWidget(self._panel)

    # ------------------------------------------------------------------
    # Step navigation
    # ------------------------------------------------------------------

    def _show_step(self) -> None:
        title, body = _STEPS[self._step]
        self._title_lbl.setText(title)
        self._body_lbl.setText(body)
        self._dots.set_step(self._step)
        self._prev_btn.setEnabled(self._step > 0)
        is_last = self._step == len(_STEPS) - 1
        self._next_btn.setText("Finish" if is_last else "Next →")

    def _on_prev(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._show_step()

    def _on_next(self) -> None:
        if self._step < len(_STEPS) - 1:
            self._step += 1
            self._show_step()
        else:
            self._finish()

    def _on_skip(self) -> None:
        self._finish()

    def _finish(self) -> None:
        self.hide()
        self.tutorial_finished.emit()
