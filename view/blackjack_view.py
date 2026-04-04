from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QMessageBox,
)
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

from model.blackjack_game import BlackjackGame
from view.card_widget import CardWidget
from view.deck_casino_view import TableZoneWidget


class BettingPanel(QWidget):
    """Shared bet-entry widget: spin box + action button."""

    bet_confirmed = pyqtSignal(int)

    def __init__(self, button_label: str = "Deal", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel("Bet: $")
        lbl.setStyleSheet("color: white; font-weight: bold;")
        self._spin = QSpinBox()
        self._spin.setMinimum(1)
        self._spin.setMaximum(1000)
        self._spin.setValue(50)
        self._spin.setSingleStep(10)
        self._spin.setFixedWidth(80)

        self._btn = QPushButton(button_label)
        self._btn.setFixedWidth(80)
        self._btn.clicked.connect(lambda: self.bet_confirmed.emit(self._spin.value()))

        layout.addWidget(lbl)
        layout.addWidget(self._spin)
        layout.addWidget(self._btn)

    def update_max(self, bankroll: int) -> None:
        m = max(1, bankroll)
        self._spin.setMaximum(m)
        if self._spin.value() > m:
            self._spin.setValue(m)

    def set_enabled(self, enabled: bool) -> None:
        self._spin.setEnabled(enabled)
        self._btn.setEnabled(enabled)


class BlackjackView(QWidget):
    """Blackjack game view.

    Holds a BlackjackGame reference and drives it directly.
    Emits back_pressed to return to the lobby.
    """

    back_pressed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._game: BlackjackGame | None = None
        self._settled: bool = False
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
        title_lbl = QLabel("Blackjack")
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

        # Dealer zone
        dealer_hdr = QLabel("Dealer")
        dealer_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dealer_hdr.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        self._dealer_zone = TableZoneWidget()
        self._dealer_cards_row = QHBoxLayout(self._dealer_zone)
        self._dealer_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dealer_value_lbl = QLabel("")
        self._dealer_value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dealer_value_lbl.setStyleSheet("color: #cccccc;")
        layout.addWidget(dealer_hdr)
        layout.addWidget(self._dealer_zone)
        layout.addWidget(self._dealer_value_lbl)

        # Player zone
        player_hdr = QLabel("Your Hand")
        player_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_hdr.setStyleSheet("color: white; font-weight: bold;")
        self._player_zone = TableZoneWidget()
        self._player_cards_row = QHBoxLayout(self._player_zone)
        self._player_cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._player_value_lbl = QLabel("")
        self._player_value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._player_value_lbl.setStyleSheet("color: #ffd700; font-weight: bold;")
        layout.addWidget(player_hdr)
        layout.addWidget(self._player_zone)
        layout.addWidget(self._player_value_lbl)

        # Result label
        self._result_lbl = QLabel("")
        self._result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._result_lbl.setStyleSheet("color: #ffd700;")
        layout.addWidget(self._result_lbl)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hit_btn = QPushButton("Hit")
        self._std_btn = QPushButton("Stand")
        self._dbl_btn = QPushButton("Double Down")
        self._spl_btn = QPushButton("Split")
        for btn in (self._hit_btn, self._std_btn, self._dbl_btn, self._spl_btn):
            btn.setFixedHeight(36)
            btn.setFixedWidth(110)
            btn.setEnabled(False)
            btn_row.addWidget(btn)
        self._hit_btn.clicked.connect(self._on_hit)
        self._std_btn.clicked.connect(self._on_stand)
        self._dbl_btn.clicked.connect(self._on_double)
        self._spl_btn.clicked.connect(self._on_split)
        layout.addLayout(btn_row)

        # Bottom: bet panel + new round button
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
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a3a1a"))

    # ── Public API ─────────────────────────────────────────────────────

    def set_game(self, game: BlackjackGame) -> None:
        self._game = game
        self._settled = False
        self._bet_panel.update_max(game.player.bankroll)
        self._reset_for_betting()

    # ── Slot handlers ──────────────────────────────────────────────────

    def _on_deal(self, bet: int) -> None:
        if self._game is None:
            return
        self._settled = False
        try:
            self._game.start_round(bet)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Bet", str(exc))
            return
        self._settle_and_refresh()

    def _on_hit(self) -> None:
        if self._game is None:
            return
        self._game.hit()
        self._settle_and_refresh()

    def _on_stand(self) -> None:
        if self._game is None:
            return
        self._game.stand()
        self._settle_and_refresh()

    def _on_double(self) -> None:
        if self._game is None:
            return
        try:
            self._game.double_down()
        except ValueError as exc:
            QMessageBox.warning(self, "Double Down", str(exc))
            return
        self._settle_and_refresh()

    def _on_split(self) -> None:
        if self._game is None:
            return
        try:
            self._game.split()
        except ValueError as exc:
            QMessageBox.warning(self, "Split", str(exc))
            return
        self._settle_and_refresh()

    def _on_new_round(self) -> None:
        if self._game is None:
            return
        self._game = BlackjackGame(self._game.player)
        self._settled = False
        self._bet_panel.update_max(self._game.player.bankroll)
        self._reset_for_betting()

    # ── Refresh / rendering ────────────────────────────────────────────

    def _settle_and_refresh(self) -> None:
        if self._game and self._game.phase == "done" and not self._settled:
            self._game.settle_bets()
            self._settled = True
        self.refresh()

    def refresh(self) -> None:
        if self._game is None:
            return
        game = self._game
        phase = game.phase

        self._bankroll_lbl.setText(f"Bankroll: ${game.player.bankroll}")

        # Dealer cards
        self._clear_layout(self._dealer_cards_row)
        if phase == "player" and game.dealer_hand.card_count() >= 2:
            for i, card in enumerate(game.dealer_hand.cards):
                self._dealer_cards_row.addWidget(CardWidget(card, face_down=(i == 1)))
            self._dealer_value_lbl.setText("Dealer: ?")
        elif phase in ("dealer", "done"):
            for card in game.dealer_hand.cards:
                self._dealer_cards_row.addWidget(CardWidget(card))
            val = game.dealer_hand.blackjack_value()
            self._dealer_value_lbl.setText(
                f"Dealer: {val}" + (" (Bust)" if val > 21 else ""))
        else:
            self._dealer_value_lbl.setText("")

        # Player cards
        self._clear_layout(self._player_cards_row)
        if game.hands:
            if phase == "player":
                hand = game.current_hand
                for card in hand.cards:
                    self._player_cards_row.addWidget(CardWidget(card))
                val = hand.blackjack_value()
                self._player_value_lbl.setText(
                    f"Your total: {val}" + (" (Bust!)" if val > 21 else ""))
            else:
                for hand in game.hands:
                    for card in hand.cards:
                        self._player_cards_row.addWidget(CardWidget(card))
                vals = [str(h.blackjack_value()) for h in game.hands]
                self._player_value_lbl.setText("Your totals: " + " | ".join(vals))
        else:
            self._player_value_lbl.setText("")

        # Action buttons
        can_act = phase == "player"
        self._hit_btn.setEnabled(can_act)
        self._std_btn.setEnabled(can_act)
        if can_act:
            two_cards = game.current_hand.card_count() == 2
            enough = game.player.bankroll >= game.bets[game.current_hand_index]
            self._dbl_btn.setEnabled(two_cards and enough)
            can_split = (two_cards and enough and
                         game.current_hand.cards[0].rank == game.current_hand.cards[1].rank)
            self._spl_btn.setEnabled(can_split)
        else:
            self._dbl_btn.setEnabled(False)
            self._spl_btn.setEnabled(False)

        self._bet_panel.set_enabled(phase == "betting")
        self._new_round_btn.setVisible(phase == "done")

        if phase == "done":
            self._show_result()
        else:
            self._result_lbl.setText("")

    def _show_result(self) -> None:
        if self._game is None:
            return
        try:
            results = self._game.get_results()
        except RuntimeError:
            return
        label_map = {
            "natural": "BLACKJACK!",
            "win":     "YOU WIN",
            "push":    "PUSH",
            "bust":    "BUST",
            "lose":    "DEALER WINS",
        }
        parts = []
        for r in results:
            label = label_map.get(r["outcome"], r["outcome"].upper())
            parts.append(f"{label}  +${r['payout']}")
        self._result_lbl.setText("  |  ".join(parts))

    def _reset_for_betting(self) -> None:
        self._clear_layout(self._dealer_cards_row)
        self._clear_layout(self._player_cards_row)
        self._dealer_value_lbl.setText("")
        self._player_value_lbl.setText("")
        self._result_lbl.setText("")
        for btn in (self._hit_btn, self._std_btn, self._dbl_btn, self._spl_btn):
            btn.setEnabled(False)
        self._bet_panel.set_enabled(True)
        self._new_round_btn.setVisible(False)

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
