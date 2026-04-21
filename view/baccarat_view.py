from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QButtonGroup, QRadioButton,
    QMessageBox,
)
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from model.baccarat_game import BaccaratGame
from view.card_widget import CardWidget
from view.blackjack_view import BettingPanel
from view.deck_casino_view import TableZoneWidget


class BaccaratView(QWidget):
    """Baccarat (Punto Banco) game view.

    Holds a BaccaratGame reference and drives it directly.
    Emits back_pressed to return to the lobby.
    Third-card drawing is shown with a short QTimer delay.
    """

    back_pressed    = pyqtSignal()
    # Emitted once per settled round: (result_str, bankroll_delta, detail_str)
    round_finished  = pyqtSignal(str, int, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._game: BaccaratGame | None = None
        self._bankroll_before: int = 0
        self._init_ui()

    # ── UI construction ────────────────────────────────────────────────

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title bar
        title_row = QHBoxLayout()
        back_btn = QPushButton("← Lobby")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.back_pressed)
        title_lbl = QLabel("Baccarat")
        title_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        self._bankroll_lbl = QLabel("Bankroll: $1000")
        self._bankroll_lbl.setStyleSheet("color: #ffd700; font-weight: bold;")
        self._bankroll_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(back_btn)
        title_row.addSpacing(8)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._bankroll_lbl)
        layout.addLayout(title_row)

        # Hands row — Punto (left) vs Banco (right)
        hands_row = QHBoxLayout()
        hands_row.setSpacing(24)

        # Punto column
        punto_col = QVBoxLayout()
        self._punto_hdr = QLabel("Punto")
        self._punto_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._punto_hdr.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._punto_hdr.setStyleSheet("color: white;")
        self._punto_zone = TableZoneWidget()
        self._punto_cards_row = QHBoxLayout(self._punto_zone)
        self._punto_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._punto_value_lbl = QLabel("")
        self._punto_value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._punto_value_lbl.setStyleSheet("color: #ffd700;")
        punto_col.addWidget(self._punto_hdr)
        punto_col.addWidget(self._punto_zone)
        punto_col.addWidget(self._punto_value_lbl)
        hands_row.addLayout(punto_col)

        # VS separator
        vs_lbl = QLabel("vs")
        vs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_lbl.setStyleSheet("color: #888888; font-size: 16pt;")
        hands_row.addWidget(vs_lbl)

        # Banco column
        banco_col = QVBoxLayout()
        self._banco_hdr = QLabel("Banco")
        self._banco_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._banco_hdr.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._banco_hdr.setStyleSheet("color: white;")
        self._banco_zone = TableZoneWidget()
        self._banco_cards_row = QHBoxLayout(self._banco_zone)
        self._banco_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._banco_value_lbl = QLabel("")
        self._banco_value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._banco_value_lbl.setStyleSheet("color: #ffd700;")
        banco_col.addWidget(self._banco_hdr)
        banco_col.addWidget(self._banco_zone)
        banco_col.addWidget(self._banco_value_lbl)
        hands_row.addLayout(banco_col)

        layout.addLayout(hands_row)

        # Result label
        self._result_lbl = QLabel("")
        self._result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._result_lbl.setStyleSheet("color: #ffd700;")
        layout.addWidget(self._result_lbl)

        # Bet type row
        bet_type_row = QHBoxLayout()
        bet_type_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bet_type_lbl = QLabel("Bet on:")
        bet_type_lbl.setStyleSheet("color: white; font-weight: bold;")
        self._bet_type_group = QButtonGroup(self)
        self._punto_radio = QRadioButton("Punto  (1:1)")
        self._banco_radio = QRadioButton("Banco  (0.95:1)")
        self._tie_radio   = QRadioButton("Tie  (8:1)")
        self._punto_radio.setChecked(True)
        for rb in (self._punto_radio, self._banco_radio, self._tie_radio):
            rb.setStyleSheet("color: white;")
            self._bet_type_group.addButton(rb)
        bet_type_row.addWidget(bet_type_lbl)
        bet_type_row.addSpacing(8)
        bet_type_row.addWidget(self._punto_radio)
        bet_type_row.addWidget(self._banco_radio)
        bet_type_row.addWidget(self._tie_radio)
        layout.addLayout(bet_type_row)

        # Bet amount + Deal / New Round
        bottom_row = QHBoxLayout()
        bottom_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bet_panel = BettingPanel("Deal")
        self._bet_panel.bet_confirmed.connect(self._on_deal)
        self._new_round_btn = QPushButton("New Round")
        self._new_round_btn.setFixedWidth(120)
        self._new_round_btn.setVisible(False)
        self._new_round_btn.clicked.connect(self._on_new_round)
        bottom_row.addWidget(self._bet_panel)
        bottom_row.addSpacing(16)
        bottom_row.addWidget(self._new_round_btn)
        layout.addLayout(bottom_row)

    def paintEvent(self, event) -> None:
        """Draw the dark purple background that distinguishes Baccarat from other views."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a1a3a"))

    # ── Public API ─────────────────────────────────────────────────────

    @property
    def current_bankroll(self) -> int:
        """Current bankroll of the active player (0 if no game loaded)."""
        return self._game.player.bankroll if self._game else 0

    def set_game(self, game: BaccaratGame) -> None:
        """Attach a BaccaratGame instance and reset the view to the betting phase."""
        self._game = game
        self._bankroll_before = game.player.bankroll
        self._bet_panel.update_max(game.player.bankroll)
        self._reset_for_betting()

    # ── Slot handlers ──────────────────────────────────────────────────

    def _on_deal(self, bet: int) -> None:
        if self._game is None:
            return
        bet_type = self._get_bet_type()
        try:
            self._game.start_round(bet, bet_type)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Bet", str(exc))
            return

        self._set_betting_controls_enabled(False)
        self._refresh_hands()

        if self._game.natural:
            QTimer.singleShot(400, self._finish_round)
        else:
            QTimer.singleShot(800, self._draw_and_finish)

    def _draw_and_finish(self) -> None:
        if self._game is None:
            return
        self._game.draw_third_card()
        self._refresh_hands()
        QTimer.singleShot(500, self._finish_round)

    def _finish_round(self) -> None:
        if self._game is None:
            return
        result = self._game.get_result()
        self._game.settle_bet()
        self._bankroll_lbl.setText(f"Bankroll: ${self._game.player.bankroll}")

        outcome = result["outcome"]
        pt = result["punto_total"]
        bt = result["banco_total"]
        payout = result["payout"]
        natural_tag = "  (Natural!)" if result["natural"] else ""
        label = {"punto_win": "PUNTO WINS", "banco_win": "BANCO WINS",
                 "tie": "TIE"}.get(outcome, outcome.upper())
        self._result_lbl.setText(
            f"{label}{natural_tag}  —  Punto {pt}  vs  Banco {bt}   Payout: ${payout}")

        # Emit history signal
        delta = self._game.player.bankroll - self._bankroll_before
        result_str = ("win" if outcome in ("punto_win", "banco_win") and delta > 0
                      else "draw" if outcome == "tie" else "loss")
        detail = "Natural!" if result["natural"] else f"Punto {pt} vs Banco {bt}"
        self._bankroll_before = self._game.player.bankroll
        self.round_finished.emit(result_str, delta, detail)

        # Highlight winner header
        self._punto_hdr.setStyleSheet(
            "color: #ffd700; font-weight: bold;"
            if outcome == "punto_win" else "color: white;")
        self._banco_hdr.setStyleSheet(
            "color: #ffd700; font-weight: bold;"
            if outcome == "banco_win" else "color: white;")

        self._new_round_btn.setVisible(True)

    def _on_new_round(self) -> None:
        if self._game is None:
            return
        self._game = BaccaratGame(self._game.player)
        self._bet_panel.update_max(self._game.player.bankroll)
        self._reset_for_betting()

    # ── Rendering helpers ──────────────────────────────────────────────

    def _get_bet_type(self) -> str:
        if self._banco_radio.isChecked():
            return "banco"
        if self._tie_radio.isChecked():
            return "tie"
        return "punto"

    def _refresh_hands(self) -> None:
        if self._game is None:
            return
        self._clear_layout(self._punto_cards_row)
        for card in self._game.punto_hand.cards:
            self._punto_cards_row.addWidget(CardWidget(card))
        self._punto_value_lbl.setText(f"Total: {self._game.punto_total()}")

        self._clear_layout(self._banco_cards_row)
        for card in self._game.banco_hand.cards:
            self._banco_cards_row.addWidget(CardWidget(card))
        self._banco_value_lbl.setText(f"Total: {self._game.banco_total()}")

    def _set_betting_controls_enabled(self, enabled: bool) -> None:
        self._bet_panel.set_enabled(enabled)
        self._punto_radio.setEnabled(enabled)
        self._banco_radio.setEnabled(enabled)
        self._tie_radio.setEnabled(enabled)

    def _reset_for_betting(self) -> None:
        self._clear_layout(self._punto_cards_row)
        self._clear_layout(self._banco_cards_row)
        self._punto_value_lbl.setText("")
        self._banco_value_lbl.setText("")
        self._result_lbl.setText("")
        self._punto_hdr.setStyleSheet(
            "color: white; font-weight: bold; font-size: 12pt;")
        self._banco_hdr.setStyleSheet(
            "color: white; font-weight: bold; font-size: 12pt;")
        self._set_betting_controls_enabled(True)
        self._new_round_btn.setVisible(False)
        if self._game:
            self._bankroll_lbl.setText(f"Bankroll: ${self._game.player.bankroll}")

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
