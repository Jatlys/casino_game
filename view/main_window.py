# QMainWindow pattern: PyQt6 Examples/5_windows/QMainWindow.py
# QStackedWidget pattern: PyQt6 Examples/5_windows/stacked_windows.py

import sys

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget,
    QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton,
)

from view.lobby_view import LobbyView
from view.deck_casino_view import DeckCasinoView


class SidebarWidget(QWidget):
    """Persistent left sidebar showing player name, score,
    and navigation buttons (Lobby, Settings).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self._name_label = QLabel("Player")       # Player name display
        self._score_label = QLabel("Score: 0")     # Cumulative score display

        self._lobby_btn = QPushButton("Lobby")
        self._settings_btn = QPushButton("Settings")

        layout.addWidget(self._name_label)
        layout.addWidget(self._score_label)
        layout.addStretch()                         # Push buttons to the bottom
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
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Casino Card Game Suite")
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)              # Set the central widget

        main_layout = QHBoxLayout(central)

        self._sidebar = SidebarWidget()             # Persistent left sidebar
        self._stack = QStackedWidget()            # Swappable view area

        main_layout.addWidget(self._sidebar)
        main_layout.addWidget(self._stack, stretch=1)

        # Register views
        self._lobby_view = LobbyView()
        self._deck_casino_view = DeckCasinoView()

        self.add_view(self._lobby_view, self.LOBBY)
        self.add_view(self._deck_casino_view, self.DECK_CASINO)

        # Connect navigation signals
        self._lobby_view.game_selected.connect(self.switch_view)
        self._deck_casino_view.back_pressed.connect(
            lambda: self.switch_view(self.LOBBY)
        )
        self._sidebar._lobby_btn.clicked.connect(
            lambda: self.switch_view(self.LOBBY)
        )

        self.switch_view(self.LOBBY)                # Start on the lobby screen

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

    def update_sidebar(self, player) -> None:
        """Push current player data to the sidebar."""
        self._sidebar.update_player_info(player.name, player.total_score)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
