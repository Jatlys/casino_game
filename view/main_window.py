# QMainWindow pattern: PyQt6 Examples/5_windows/QMainWindow.py
# QStackedWidget pattern: PyQt6 Examples/5_windows/stacked_windows.py

import sys

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget,
    QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox,
)
from PyQt6.QtGui import QFont

from controller.game_manager import GameManager
from model.player import Player
from view.lobby_view import LobbyView
from view.deck_casino_view import DeckCasinoView


class PlayerSetupDialog(QDialog):
    """Modal dialog for entering player names before a Deck Casino game.

    Requires at least 2 names; supports up to 4 players.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Player Setup")
        self.setFixedWidth(320)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter player names (2–4 players):"))

        self._name_edits: list[QLineEdit] = []
        form = QFormLayout()
        for i in range(4):
            edit = QLineEdit()
            edit.setPlaceholderText(f"Player {i + 1}")
            form.addRow(f"Player {i + 1}:", edit)
            self._name_edits.append(edit)

        # Pre-fill two default names so the dialog is ready immediately
        self._name_edits[0].setText("Player 1")
        self._name_edits[1].setText("Player 2")

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_player_names(self) -> list[str]:
        return [e.text().strip() for e in self._name_edits if e.text().strip()]


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
        self._settings_btn = QPushButton("Settings")

        layout.addWidget(self._name_label)
        layout.addWidget(self._score_label)
        layout.addStretch()                     # Push buttons to the bottom
        layout.addWidget(self._lobby_btn)
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

    def __init__(self) -> None:
        super().__init__()
        self._game_manager = GameManager()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Casino Card Game Suite")
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

        self.add_view(self._lobby_view,       self.LOBBY)
        self.add_view(self._deck_casino_view, self.DECK_CASINO)

        # Connect navigation signals
        self._lobby_view.game_selected.connect(self._on_game_selected)
        self._deck_casino_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._sidebar._lobby_btn.clicked.connect(
            lambda: self.switch_view(self.LOBBY)
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
        # Blackjack and Baccarat handled in Week 5/6

    def _launch_deck_casino(self) -> None:
        # Step 1: player names
        dialog = PlayerSetupDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        names = dialog.get_player_names()
        if len(names) < 2:
            QMessageBox.warning(
                self, "Not enough players",
                "Please enter at least 2 player names."
            )
            return

        # Step 2: tutorial mode prompt
        tutorial_dialog = TutorialModeDialog(self)
        tutorial_mode = tutorial_dialog.exec() == QDialog.DialogCode.Accepted

        players = [Player(name) for name in names]
        self._game_manager.start_deck_casino(players)

        self._deck_casino_view.refresh(self._game_manager.active_game)
        self.switch_view(self.DECK_CASINO)
        self.update_sidebar(self._game_manager.active_game.current_player)

        if tutorial_mode:
            self._deck_casino_view.start_tutorial()

    # Deck Casino actions

    def _on_deck_casino_take(self, card, take: frozenset) -> None:
        game = self._game_manager.active_game
        try:
            game.play_card(card, take)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Take", str(e))
            return
        self._after_deck_casino_action()

    def _on_deck_casino_place(self, card) -> None:
        self._game_manager.active_game.play_card(card, None)
        self._after_deck_casino_action()

    def _after_deck_casino_action(self) -> None:
        game = self._game_manager.active_game

        if game.is_round_over():
            game.end_round()

            scores = "\n".join(
                f"  {p.name}: {p.total_score} pts" for p in game.players
            )

            if game.has_winner():
                winner = max(game.players, key=lambda p: p.total_score)
                QMessageBox.information(
                    self, "Game Over",
                    f"{winner.name} wins with {winner.total_score} points!\n\n"
                    f"Final scores:\n{scores}"
                )
                self.switch_view(self.LOBBY)
                return

            QMessageBox.information(
                self, "Round Over",
                f"Round complete! Starting a new round.\n\nScores:\n{scores}"
            )
            game.start_game()

        self._deck_casino_view.refresh(game)
        self.update_sidebar(game.current_player)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
