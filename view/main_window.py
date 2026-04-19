# QMainWindow pattern: PyQt6 Examples/5_windows/QMainWindow.py
# QStackedWidget pattern: PyQt6 Examples/5_windows/stacked_windows.py

import sys

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget,
    QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton, QButtonGroup, QRadioButton,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QFrame,
    QInputDialog,
)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QFont, QIcon

from controller.game_manager import GameManager
from model.player import Player
from model.ai_opponent import AIOpponent
from model.file_manager import FileManager
from view.lobby_view import LobbyView
from view.deck_casino_view import DeckCasinoView
from view.blackjack_view import BlackjackView
from view.baccarat_view import BaccaratView
from view.game_history_view import GameHistoryView, HistoryEntry
from view.drawn_assets import make_window_icon, RoundResultOverlay


class PlayerSetupDialog(QDialog):
    """Two-step player setup dialog.

    Step 1 — Mode selection:
        • Player vs Player  →  choose 2/3/4 players + names
        • Player vs Computer  →  enter your name + choose AI difficulty

    get_players() returns a ready-to-use list[Player].
    """

    _DIFFICULTY_DESCRIPTIONS = {
        "easy":   "Plays random legal moves — great for beginners.",
        "medium": "Uses basic strategy: sweeps and maximises cards taken.",
        "hard":   "Optimal play: captures prize cards and avoids easy sweeps.",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Player Setup")
        self.setFixedWidth(380)
        self._init_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── Mode selection ──────────────────────────────────────────
        mode_label = QLabel("Game Mode:")
        mode_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        root.addWidget(mode_label)

        self._pvp_radio = QRadioButton("Player vs Player")
        self._pvc_radio = QRadioButton("Player vs Computer")
        self._pvp_radio.setChecked(True)

        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self._pvp_radio)
        self._mode_group.addButton(self._pvc_radio)

        root.addWidget(self._pvp_radio)
        root.addWidget(self._pvc_radio)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # ── Stacked content area ────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_pvp_page())   # index 0
        self._stack.addWidget(self._build_pvc_page())   # index 1
        root.addWidget(self._stack)

        # ── OK / Cancel ─────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        # Connect mode radios → switch stack page
        self._pvp_radio.toggled.connect(
            lambda checked: self._stack.setCurrentIndex(0) if checked else None
        )
        self._pvc_radio.toggled.connect(
            lambda checked: self._stack.setCurrentIndex(1) if checked else None
        )

    def _build_pvp_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Number of players
        count_label = QLabel("Number of players:")
        count_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(count_label)

        count_row = QHBoxLayout()
        self._count_group = QButtonGroup(self)
        self._count_radios: list[QRadioButton] = []
        for n in (2, 3, 4):
            rb = QRadioButton(str(n))
            if n == 2:
                rb.setChecked(True)
            self._count_group.addButton(rb, n)
            count_row.addWidget(rb)
            self._count_radios.append(rb)
        count_row.addStretch()
        layout.addLayout(count_row)

        # Name fields
        layout.addSpacing(4)
        self._pvp_name_edits: list[QLineEdit] = []
        self._pvp_form = QFormLayout()
        defaults = ["Player 1", "Player 2", "", ""]
        for i in range(4):
            edit = QLineEdit()
            edit.setText(defaults[i])
            edit.setPlaceholderText(f"Player {i + 1}")
            self._pvp_form.addRow(f"Player {i + 1}:", edit)
            self._pvp_name_edits.append(edit)
        layout.addLayout(self._pvp_form)

        # Wire count radios → show/hide extra fields
        self._count_group.idToggled.connect(self._update_pvp_fields)
        self._update_pvp_fields()

        return page

    def _build_pvc_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Human name
        form = QFormLayout()
        self._human_name_edit = QLineEdit("Player 1")
        form.addRow("Your name:", self._human_name_edit)
        layout.addLayout(form)

        layout.addSpacing(4)

        # Difficulty
        diff_label = QLabel("AI Difficulty:")
        diff_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(diff_label)

        self._diff_group = QButtonGroup(self)
        self._diff_radios: dict[str, QRadioButton] = {}
        for key, label in (("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")):
            rb = QRadioButton(label)
            if key == "medium":
                rb.setChecked(True)
            self._diff_group.addButton(rb)
            self._diff_radios[key] = rb
            layout.addWidget(rb)

        # Description label — updates when difficulty changes
        self._diff_desc = QLabel(self._DIFFICULTY_DESCRIPTIONS["medium"])
        self._diff_desc.setWordWrap(True)
        self._diff_desc.setStyleSheet("color: #555555; font-style: italic;")
        layout.addWidget(self._diff_desc)

        for key, rb in self._diff_radios.items():
            rb.toggled.connect(
                lambda checked, k=key: self._diff_desc.setText(
                    self._DIFFICULTY_DESCRIPTIONS[k]
                ) if checked else None
            )

        return page

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_pvp_fields(self) -> None:
        """Show name fields 1..N, hide the rest."""
        n = self._count_group.checkedId()
        for i, edit in enumerate(self._pvp_name_edits):
            visible = i < n
            # Show/hide both the label and field via the form row
            label_item = self._pvp_form.itemAt(i * 2)
            field_item = self._pvp_form.itemAt(i * 2 + 1)
            if label_item and label_item.widget():
                label_item.widget().setVisible(visible)
            if field_item and field_item.widget():
                field_item.widget().setVisible(visible)

    def _selected_difficulty(self) -> str:
        for key, rb in self._diff_radios.items():
            if rb.isChecked():
                return key
        return "medium"

    def _on_accept(self) -> None:
        if self._pvp_radio.isChecked():
            names = [
                e.text().strip()
                for e in self._pvp_name_edits
                if e.text().strip()
            ]
            if len(names) < 2:
                QMessageBox.warning(
                    self, "Not enough players",
                    "Please enter at least 2 player names."
                )
                return
        else:
            name = self._human_name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Name required", "Please enter your name.")
                return
        self.accept()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_players(self) -> list[Player]:
        """Return a Player list ready to pass to DeckCasinoGame.

        Human players are initialised with their persisted bankroll so that
        a balance built up in Blackjack / Baccarat carries over here too.
        """
        if self._pvp_radio.isChecked():
            names = [
                e.text().strip()
                for e in self._pvp_name_edits
                if e.text().strip()
            ]
            return [Player(n, bankroll=FileManager.load_bankroll(n)) for n in names]
        else:
            human = self._human_name_edit.text().strip() or "Player 1"
            diff  = self._selected_difficulty()
            return [
                Player(human, bankroll=FileManager.load_bankroll(human)),
                Player("Computer", is_ai=True, difficulty=diff),
            ]


class TutorialModeDialog(QDialog):
    """Modal dialog asking whether the player wants a guided tutorial."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tutorial Mode")
        self.setFixedWidth(360)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Would you like to play Tutorial Mode?")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setWordWrap(True)
        layout.addWidget(title)

        desc = QLabel(
            "Tutorial Mode walks you through the rules step by step "
            "— how to take cards, earn sweeps, collect special cards, "
            "and rack up points. You can skip it at any time."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        buttons = QDialogButtonBox()
        yes_btn = buttons.addButton("Yes, start tutorial", QDialogButtonBox.ButtonRole.AcceptRole)
        no_btn  = buttons.addButton("No, just play",       QDialogButtonBox.ButtonRole.RejectRole)
        yes_btn.setDefault(True)
        _ = no_btn   # referenced to satisfy linter
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SidebarWidget(QWidget):
    """Persistent left sidebar showing player name, score,
    and navigation buttons (Lobby, Settings).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self._name_label  = QLabel("Player")    # Player name display
        self._score_label = QLabel("Score: 0")  # Cumulative score display

        self._lobby_btn    = QPushButton("Lobby")
        self._history_btn  = QPushButton("History")
        self._settings_btn = QPushButton("Settings")

        layout.addWidget(self._name_label)
        layout.addWidget(self._score_label)
        layout.addStretch()                     # Push buttons to the bottom
        layout.addWidget(self._lobby_btn)
        layout.addWidget(self._history_btn)
        layout.addWidget(self._settings_btn)

        self.setLayout(layout)
        self.setFixedWidth(160)

    def update_player_info(self, name: str, score: int) -> None:
        """Refresh the sidebar labels with current player data."""
        self._name_label.setText(name)
        self._score_label.setText(f"Score: {score}")


class MainWindow(QMainWindow):
    """Application shell: persistent sidebar + QStackedWidget main area.

    Views are registered by name and switched via switch_view().
    Blackjack and Baccarat views are added in Week 6.
    """

    # View name constants
    LOBBY       = "lobby"
    DECK_CASINO = "Deck Casino"
    BLACKJACK   = "Blackjack"
    BACCARAT    = "Baccarat"
    HISTORY     = "History"

    def __init__(self) -> None:
        super().__init__()
        self._game_manager = GameManager()
        self._move_history: list[dict] = []
        self._player_names: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Casino Card Game Suite")
        self.setWindowIcon(QIcon(make_window_icon()))
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)      # Set the central widget

        main_layout = QHBoxLayout(central)

        self._sidebar = SidebarWidget()     # Persistent left sidebar
        self._stack   = QStackedWidget()    # Swappable view area

        main_layout.addWidget(self._sidebar)
        main_layout.addWidget(self._stack, stretch=1)

        # Register views
        self._lobby_view       = LobbyView()
        self._deck_casino_view = DeckCasinoView()
        self._blackjack_view   = BlackjackView()
        self._baccarat_view    = BaccaratView()
        self._history_view     = GameHistoryView()

        self.add_view(self._lobby_view,       self.LOBBY)
        self.add_view(self._deck_casino_view, self.DECK_CASINO)
        self.add_view(self._blackjack_view,   self.BLACKJACK)
        self.add_view(self._baccarat_view,    self.BACCARAT)
        self.add_view(self._history_view,     self.HISTORY)

        # Connect navigation signals
        self._lobby_view.game_selected.connect(self._on_game_selected)
        self._deck_casino_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._blackjack_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._baccarat_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._history_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._sidebar._lobby_btn.clicked.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._sidebar._history_btn.clicked.connect(
            lambda: self.switch_view(self.HISTORY)
        )

        # Connect Deck Casino action signals
        self._deck_casino_view.take_requested.connect(self._on_deck_casino_take)
        self._deck_casino_view.place_requested.connect(self._on_deck_casino_place)


        self.switch_view(self.LOBBY) # Start on the lobby screen

    # View switching

    def add_view(self, widget: QWidget, name: str) -> None:
        """Register a view widget under the given name."""
        widget.setObjectName(name)
        self._stack.addWidget(widget)

    def switch_view(self, name: str) -> None:
        """Display the view registered under name."""
        for i in range(self._stack.count()):
            if self._stack.widget(i).objectName() == name:
                self._stack.setCurrentIndex(i)
                return

    # Sidebar helpers

    def update_sidebar(self, player: Player) -> None:
        """Push current player data to the sidebar."""
        self._sidebar.update_player_info(player.name, player.total_score)

    # Game launch

    def _on_game_selected(self, game_name: str) -> None:
        if game_name == self.DECK_CASINO:
            self._launch_deck_casino()
        elif game_name == self.BLACKJACK:
            self._launch_blackjack()
        elif game_name == self.BACCARAT:
            self._launch_baccarat()

    def _launch_deck_casino(self) -> None:
        # Step 1: mode + player setup
        dialog = PlayerSetupDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        players = dialog.get_players()
        self._player_names = [p.name for p in players]
        self._move_history = []

        # Step 2: check for a matching roster save file and offer to resume
        saved = FileManager.load(self._player_names)
        if saved is not None:
            reply = QMessageBox.question(
                self, "Resume Saved Game",
                f"A saved game was found for {', '.join(self._player_names)}. "
                "Resume where you left off?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                game, self._move_history = saved
                self._game_manager._active_game = game
                self._deck_casino_view.refresh(game)
                self.switch_view(self.DECK_CASINO)
                self.update_sidebar(game.current_player)
                return

        # Step 3: tutorial mode prompt
        tutorial_dialog = TutorialModeDialog(self)
        tutorial_mode = tutorial_dialog.exec() == QDialog.DialogCode.Accepted

        self._game_manager.start_deck_casino(players)

        self._deck_casino_view.refresh(self._game_manager.active_game, animate_deal=True)
        self.switch_view(self.DECK_CASINO)
        self.update_sidebar(self._game_manager.active_game.current_player)

        if tutorial_mode:
            self._deck_casino_view.start_tutorial()

    def _launch_blackjack(self) -> None:
        name, ok = QInputDialog.getText(self, "Player Name", "Enter your name:")
        if not ok or not name.strip():
            return
        from model.blackjack_game import BlackjackGame
        pname = name.strip()
        # Load this player's saved bankroll — each name has its own balance
        saved_bankroll = FileManager.load_bankroll(pname)
        player = Player(pname, bankroll=saved_bankroll)
        self._blackjack_view.set_game(BlackjackGame(player))
        # Re-connect so the player name and bankroll saving are wired per session
        try:
            self._blackjack_view.round_finished.disconnect()
        except TypeError:
            pass
        self._blackjack_view.round_finished.connect(
            lambda result, delta, detail, n=pname:
                self._on_blackjack_round_finished(n, result, delta, detail)
        )
        self.switch_view(self.BLACKJACK)

    def _on_blackjack_round_finished(self, player_name: str, result: str,
                                     delta: int, detail: str) -> None:
        """Save bankroll and record history after a Blackjack round."""
        FileManager.save_bankroll(player_name, self._blackjack_view.current_bankroll)
        self._history_view.add_entry(
            HistoryEntry(game="Blackjack", player=player_name, result=result,
                         delta=delta, detail=detail)
        )

    def _launch_baccarat(self) -> None:
        name, ok = QInputDialog.getText(self, "Player Name", "Enter your name:")
        if not ok or not name.strip():
            return
        from model.baccarat_game import BaccaratGame
        pname = name.strip()
        # Load this player's saved bankroll — each name has its own balance
        saved_bankroll = FileManager.load_bankroll(pname)
        player = Player(pname, bankroll=saved_bankroll)
        self._baccarat_view.set_game(BaccaratGame(player))
        # Re-connect so the player name and bankroll saving are wired per session
        try:
            self._baccarat_view.round_finished.disconnect()
        except TypeError:
            pass
        self._baccarat_view.round_finished.connect(
            lambda result, delta, detail, n=pname:
                self._on_baccarat_round_finished(n, result, delta, detail)
        )
        self.switch_view(self.BACCARAT)

    def _on_baccarat_round_finished(self, player_name: str, result: str,
                                    delta: int, detail: str) -> None:
        """Save bankroll and record history after a Baccarat round."""
        FileManager.save_bankroll(player_name, self._baccarat_view.current_bankroll)
        self._history_view.add_entry(
            HistoryEntry(game="Baccarat", player=player_name, result=result,
                         delta=delta, detail=detail)
        )

    # Deck Casino actions

    # ── Capture-event helpers ─────────────────────────────────────────────────

    def _show_capture_events(self, player, card, take, sweeps_before: dict) -> None:
        """Detect notable captures and show the appropriate overlays."""
        hint = self._deck_casino_view.is_hint_mode
        taken = (frozenset(take) | {card}) if take else frozenset()

        # Sweep
        if player.sweeps > sweeps_before.get(player, 0):
            hint_text = (
                "Capturing all table cards at once earns 1 sweep point, "
                "awarded at the end of the round."
            ) if hint else ""
            self._deck_casino_view.show_sweep_flash(player.name, hint_text)

        if not taken:
            return

        # Aces, Diamond-10, Spade-2
        aces   = [c for c in taken if c.rank == "A"]
        has_d10 = any(c.suit == "Diamonds" and c.rank == "10" for c in taken)
        has_s2  = any(c.suit == "Spades"   and c.rank == "2"  for c in taken)

        events = []
        hints  = []

        if aces:
            n = len(aces)
            pts = n
            events.append(f"{'an Ace' if n == 1 else f'{n} Aces'} (+{pts} pt{'s' if pts > 1 else ''})")
            if hint:
                hints.append("Each Ace collected earns 1 point at round end.")

        if has_d10:
            events.append("the 10\u2666 (+2 pts)")
            if hint:
                hints.append("The 10 of Diamonds earns 2 points for its holder at round end.")

        if has_s2:
            events.append("the 2\u2660 (+1 pt)")
            if hint:
                hints.append("The 2 of Spades earns 1 point for its holder at round end.")

        if not events:
            return

        accent   = "#ff9800" if player.is_ai else "#4caf50"
        title    = f"{player.name} captured {', '.join(events)}"
        subtitle = "  \u2022  ".join(hints) if hints else ""
        self._deck_casino_view.show_point_toast(title, subtitle, accent)

    # ── Deck Casino action handlers ───────────────────────────────────────────

    def _record_deck_casino_round(self, game) -> None:
        """Add one HistoryEntry per player for the just-ended Deck Casino round."""
        ranked = sorted(game.players, key=lambda p: p.total_score, reverse=True)
        for rank, player in enumerate(ranked, start=1):
            placement = {1: "1st", 2: "2nd", 3: "3rd"}.get(rank, f"#{rank}")
            result_str = "win" if rank == 1 else "loss"
            detail = f"{player.sweeps} sweep(s)" if player.sweeps else ""
            self._history_view.add_entry(
                HistoryEntry(
                    game="Deck Casino",
                    player=player.name,
                    result=placement,
                    delta=player.total_score,
                    detail=detail,
                )
            )

    def _on_deck_casino_take(self, card, take: frozenset) -> None:
        game = self._game_manager.active_game
        player = game.current_player
        player_name = player.name
        table_before = game.table_cards
        sweeps_before = {p: p.sweeps for p in game.players}
        try:
            game.play_card(card, take)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Take", str(e))
            return
        self._move_history.append(
            FileManager.record_move(player_name, card, take, table_before)
        )
        self._show_capture_events(player, card, take, sweeps_before)
        self._after_deck_casino_action()

    def _on_deck_casino_place(self, card) -> None:
        game = self._game_manager.active_game
        player_name = game.current_player.name
        table_before = game.table_cards
        game.play_card(card, None)
        self._move_history.append(
            FileManager.record_move(player_name, card, None, table_before)
        )
        self._after_deck_casino_action()

    def _after_deck_casino_action(self) -> None:
        game = self._game_manager.active_game

        # Auto-play all consecutive AI turns before handing back to the human.
        # Also skip over any human player whose hand is empty (deck already
        # exhausted), so the AI can finish playing its remaining cards.
        # processEvents() keeps the UI responsive during long AI chains.
        while not game.is_round_over():
            cp = game.current_player
            if cp.is_ai:
                card, take = AIOpponent.decide_action(game, cp.difficulty)
                sweeps_before = {p: p.sweeps for p in game.players}
                game.play_card(card, take)
                self._show_capture_events(cp, card, take, sweeps_before)
                QCoreApplication.processEvents()
            elif cp.hand.is_empty():
                game.advance_turn()
            else:
                break

        if game.is_round_over():
            game.end_round()
            self._record_deck_casino_round(game)

            is_game_over = game.has_winner()
            RoundResultOverlay(game.players, is_game_over=is_game_over, parent=self).exec()

            if is_game_over:
                self.switch_view(self.LOBBY)
                return

            game.start_game()
            self._deck_casino_view.refresh(game, animate_deal=True)
        else:
            self._deck_casino_view.refresh(game)
        self.update_sidebar(game.current_player)
        FileManager.save(game, self._move_history, self._player_names or None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
