# Deck Casino table view — connected to DeckCasinoGame via signals (Week 3).

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, pyqtSignal

from view.card_widget import CardWidget, CARD_H
from view.player_badge_widget import PlayerBadgeWidget
from view.game_instructions.deck_casino import DeckCasinoInstructionsDialog
from view.deck_casino_tutorial import TutorialOverlay
from view.drawn_assets import SweepFlashOverlay, PointToastOverlay


class TableZoneWidget(QWidget):
    """QPainter-drawn green felt zone used for table card placement."""

    def __init__(self, zone_label: str = "", parent=None) -> None:
        super().__init__(parent)
        self._zone_label = zone_label
        self.setMinimumHeight(CARD_H + 48)

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
    """Interactive table view for Deck Casino.

    Signals:
        back_pressed:    user clicked Back to Lobby
        take_requested:  (Card, frozenset[Card]) — play card and take table cards
        place_requested: (Card,) — play card onto the table
    """

    back_pressed    = pyqtSignal()
    take_requested  = pyqtSignal(object, object)   # (Card, frozenset[Card])
    place_requested = pyqtSignal(object)           # Card

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_hand_card = None
        self._selected_table_cards: set = set()
        self._table_card_widgets: list[tuple] = []  # (Card, CardWidget)
        self._hand_card_widgets:  list[tuple] = []  # (Card, CardWidget)
        self._tutorial_overlay = TutorialOverlay(self)
        self._sweep_flash = SweepFlashOverlay(self)
        self._point_toast = PointToastOverlay(self)
        self._current_game = None
        self._init_ui()

    # UI

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title bar
        title_row = QHBoxLayout()
        title_lbl = QLabel("Deck Casino")
        title_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        self._turn_label = QLabel("")
        self._turn_label.setStyleSheet("color: #ffd700; font-weight: bold;")
        self._turn_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        title_row.addWidget(title_lbl)
        title_row.addWidget(self._turn_label)
        layout.addLayout(title_row)

        # Scores / stock row
        scores_widget = QWidget()
        scores_widget.setStyleSheet("background: transparent;")
        self._scores_layout = QHBoxLayout(scores_widget)
        self._scores_layout.setSpacing(12)
        self._scores_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scores_widget)

        # Table card zone (centre of the table)
        self._table_zone = TableZoneWidget("Table Cards")
        self._table_card_layout = QHBoxLayout(self._table_zone)
        self._table_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table_card_layout.setSpacing(10)
        self._table_card_layout.setContentsMargins(12, 28, 12, 12)
        layout.addWidget(self._table_zone, stretch=2)

        # Player hand zone (bottom of the table)
        hand_frame = QFrame()
        hand_frame.setStyleSheet("background: #2e7d32; border-radius: 10px;")
        hand_layout_v = QVBoxLayout(hand_frame)
        hand_layout_v.setContentsMargins(12, 8, 12, 8)
        hand_layout_v.setSpacing(6)

        self._player_name_label = QLabel("Your Hand")
        self._player_name_label.setStyleSheet("color: white; font-weight: bold;")
        hand_layout_v.addWidget(self._player_name_label)

        self._hand_card_layout = QHBoxLayout()
        self._hand_card_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._hand_card_layout.setSpacing(10)
        hand_layout_v.addLayout(self._hand_card_layout)

        layout.addWidget(hand_frame, stretch=1)

        # Tutorial overlay (hidden by default; shown when tutorial mode is active)
        layout.addWidget(self._tutorial_overlay)

        # Action buttons
        btn_row = QHBoxLayout()
        self._back_btn  = QPushButton("← Lobby")
        self._take_btn  = QPushButton("Take Cards")
        self._place_btn = QPushButton("Place Card")
        self._take_btn.setEnabled(False)
        self._place_btn.setEnabled(False)
        self._how_to_btn = QPushButton("How to Play")
        self._hint_btn   = QPushButton("Hint Mode: Off")
        self._hint_btn.setCheckable(True)
        self._hint_btn.setStyleSheet(
            "QPushButton { color: #aaaaaa; background: #1b3a1b; "
            "border: 1px solid #555; border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:checked { color: #ffd700; background: #2a4a1b; "
            "border-color: #ffd700; }"
            "QPushButton:hover { border-color: #aaaaaa; }"
        )
        self._back_btn.clicked.connect(lambda: self.back_pressed.emit())
        self._how_to_btn.clicked.connect(self._on_how_to_clicked)
        self._hint_btn.toggled.connect(self._on_hint_toggled)
        self._take_btn.clicked.connect(self._on_take_clicked)
        self._place_btn.clicked.connect(self._on_place_clicked)
        btn_row.addWidget(self._back_btn)
        btn_row.addWidget(self._how_to_btn)
        btn_row.addWidget(self._hint_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._place_btn)
        btn_row.addWidget(self._take_btn)
        layout.addLayout(btn_row)

    # Paint event

    def paintEvent(self, event) -> None:
        """Dark felt background for the whole game view."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a3a1a"))

    # Public

    def refresh(self, game) -> None:
        """Rebuild the entire view from the current game state."""
        self._current_game = game
        self._selected_hand_card = None
        self._selected_table_cards = set()

        self._turn_label.setText(f"{game.current_player.name}'s Turn")
        self._player_name_label.setText(f"{game.current_player.name}'s Hand")

        self._rebuild_scores(game.players, len(game.deck))
        self._rebuild_table_cards(game.table_cards)
        self._rebuild_hand_cards(game.current_player.hand.cards)
        self._update_buttons()

    def _on_hint_toggled(self, checked: bool) -> None:
        self._hint_btn.setText("Hint Mode: On" if checked else "Hint Mode: Off")
        CardWidget.set_hint_mode(checked)
        if self._current_game is not None:
            self.refresh(self._current_game)

    @property
    def is_hint_mode(self) -> bool:
        """True when hint mode is currently active."""
        return self._hint_btn.isChecked()

    def show_sweep_flash(self, player_name: str = "", hint_text: str = "") -> None:
        """Trigger the sweep flash overlay for the given player."""
        self._sweep_flash.flash(player_name, hint_text)

    def show_point_toast(self, title: str, subtitle: str = "",
                         accent: str = "#ffd700") -> None:
        """Show a brief capture-event toast banner."""
        self._point_toast.show_event(title, subtitle, accent)

    def start_tutorial(self) -> None:
        """Show the step-by-step tutorial overlay above the action buttons."""
        self._tutorial_overlay._step = 0
        self._tutorial_overlay._show_step()
        self._tutorial_overlay.show()

    # Private rebuild helpers

    @staticmethod
    def _pending_points(player, all_players: list) -> int:
        """Projected points this player will earn at round end from current collection."""
        pts = 0
        pts += player.sweeps
        pts += sum(1 for c in player.collection if c.rank == "A")

        # Most cards (tie = no point)
        max_cards = max(len(p.collection) for p in all_players)
        if (len(player.collection) == max_cards and
                sum(1 for p in all_players if len(p.collection) == max_cards) == 1):
            pts += 1

        # Most spades (tie = no point) — 2 points
        spade_counts = {p: sum(1 for c in p.collection if c.suit == "Spades")
                        for p in all_players}
        max_sp = max(spade_counts.values())
        if (spade_counts[player] == max_sp and
                sum(1 for p in all_players if spade_counts[p] == max_sp) == 1):
            pts += 2

        # Diamond-10 holder — 2 points
        if any(c.suit == "Diamonds" and c.rank == "10" for c in player.collection):
            pts += 2

        # Spade-2 holder — 1 point
        if any(c.suit == "Spades" and c.rank == "2" for c in player.collection):
            pts += 1

        return pts

    def _rebuild_scores(self, players, stock_count: int) -> None:
        self._clear_layout(self._scores_layout)
        current = players[self._current_game._turn_index] if self._current_game else None

        # Build badges, then equalise their widths
        badges = []
        for player in players:
            pending = self._pending_points(player, players)
            badge = PlayerBadgeWidget(player, is_current=(player is current),
                                      pending_pts=pending)
            badges.append(badge)

        max_w = max(b.minimumWidth() for b in badges)
        for b in badges:
            b.setFixedWidth(max_w)

        # Centre the badges; Stock label pinned to the right
        self._scores_layout.addStretch(1)
        for b in badges:
            self._scores_layout.addWidget(b)
        self._scores_layout.addStretch(1)
        stock_lbl = QLabel(f"Stock: {stock_count}")
        stock_lbl.setStyleSheet("color: #aaaaaa;")
        self._scores_layout.addWidget(stock_lbl)

    def _rebuild_table_cards(self, cards: list) -> None:
        self._clear_layout(self._table_card_layout)
        self._table_card_widgets = []
        if not cards:
            placeholder = QLabel("Table is empty")
            placeholder.setStyleSheet("color: #ffffff80;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table_card_layout.addWidget(placeholder)
            return
        for card in cards:
            w = CardWidget(card)
            w.clicked.connect(lambda c=card, widget=w: self._on_table_card_clicked(c, widget))
            self._table_card_layout.addWidget(w)
            self._table_card_widgets.append((card, w))

    def _rebuild_hand_cards(self, cards: list) -> None:
        self._clear_layout(self._hand_card_layout)
        self._hand_card_widgets = []
        for card in cards:
            w = CardWidget(card)
            w.clicked.connect(lambda c=card, widget=w: self._on_hand_card_clicked(c, widget))
            self._hand_card_layout.addWidget(w)
            self._hand_card_widgets.append((card, w))
        self._hand_card_layout.addStretch()

    # Interaction handlers

    def _on_how_to_clicked(self) -> None:
        DeckCasinoInstructionsDialog(self).exec()

    def _on_hand_card_clicked(self, card, widget: CardWidget) -> None:
        if self._selected_hand_card == card:
            # Deselect
            self._selected_hand_card = None
            widget.set_selected(False)
        else:
            # Deselect previous hand card
            for _, w in self._hand_card_widgets:
                w.set_selected(False)
            self._selected_hand_card = card
            widget.set_selected(True)
            # Clear table selections when hand card changes
            self._selected_table_cards = set()
            for _, w in self._table_card_widgets:
                w.set_selected(False)
        self._update_buttons()

    def _on_table_card_clicked(self, card, widget: CardWidget) -> None:
        if self._selected_hand_card is None:
            return  # must select a hand card first
        if card in self._selected_table_cards:
            self._selected_table_cards.discard(card)
            widget.set_selected(False)
        else:
            self._selected_table_cards.add(card)
            widget.set_selected(True)
        self._update_buttons()

    def _on_take_clicked(self) -> None:
        if self._selected_hand_card and self._selected_table_cards:
            self.take_requested.emit(
                self._selected_hand_card,
                frozenset(self._selected_table_cards),
            )

    def _on_place_clicked(self) -> None:
        if self._selected_hand_card:
            self.place_requested.emit(self._selected_hand_card)

    def _update_buttons(self) -> None:
        hand_ok  = self._selected_hand_card is not None
        table_ok = len(self._selected_table_cards) > 0
        self._place_btn.setEnabled(hand_ok)
        self._take_btn.setEnabled(hand_ok and table_ok)

    # Utility

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()        # hide immediately; deleteLater fires next event loop cycle
                w.deleteLater()
