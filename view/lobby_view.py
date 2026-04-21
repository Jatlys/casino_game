# Game selection lobby.
# All banner art is drawn with QPainter — no external image files required.

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF, pyqtSignal


class GameBannerWidget(QWidget):
    """QPainter-drawn game card showing a card-fan illustration,
    game title, short description, and a Play button.
    """

    play_clicked = pyqtSignal(str)  # emits the game name string

    def __init__(self, game_name: str, description: str,
                 color: QColor, parent=None) -> None:
        super().__init__(parent)
        self._game_name = game_name
        self._description = description
        self._color = color
        self.setFixedSize(220, 300)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 155, 12, 12)  # reserve top 155 px for QPainter art
        layout.addStretch()

        play_btn = QPushButton(f"Play {self._game_name}")
        play_btn.setFixedHeight(36)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self._game_name))
        layout.addWidget(play_btn)

    # Paint event

    def paintEvent(self, event) -> None:
        """Draw the coloured header, card-fan illustration, and text for this banner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_header(painter)
        self._draw_card_fan(painter)
        self._draw_text(painter)

    # Drawing helpers

    def _draw_header(self, painter: QPainter) -> None:
        """Coloured header band that fills the top of the banner."""
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), 148), 10, 10)
        # Square off the bottom edge of the rounded header
        painter.drawRect(QRectF(0, 135, self.width(), 13))

    def _draw_card_fan(self, painter: QPainter) -> None:
        """Three overlapping white card shapes fanned out in the header."""
        cx, cy = self.width() // 2, 75
        fans = [(-28, 8, -18), (0, 0, 0), (28, 8, 18)]  # (dx, dy, rotation)

        for dx, dy, angle in fans:
            painter.save()
            painter.translate(cx + dx, cy + dy)
            painter.rotate(angle)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(QPen(QColor("#cccccc"), 1))
            painter.drawRoundedRect(QRectF(-20, -30, 40, 58), 4, 4)
            painter.restore()

    def _draw_text(self, painter: QPainter) -> None:
        """Game title and description text below the header."""
        # Game title
        painter.setPen(QPen(QColor("#222222")))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(QRect(0, 150, self.width(), 24),
                         Qt.AlignmentFlag.AlignCenter, self._game_name)

        # Short description
        painter.setPen(QPen(QColor("#555555")))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRect(12, 174, self.width() - 24, 36),
                         Qt.AlignmentFlag.AlignCenter, self._description)


class LobbyView(QWidget):
    """Game selection screen with QPainter-drawn banners for each available game."""

    game_selected = pyqtSignal(str)  # forwarded from GameBannerWidget.play_clicked

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Casino Card Game Suite")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Select a game to begin")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #777777;")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Game banners row
        banners_row = QHBoxLayout()
        banners_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banners_row.setSpacing(28)

        games = [
            ("Deck Casino", "Finnish card-taking game\nwith AI opponent",  QColor("#2e7d32")),
            ("Blackjack",   "Beat the dealer to 21\nwithout going bust",   QColor("#1565c0")),
            ("Baccarat",    "Bet on Punto, Banco\nor Tie",                  QColor("#6a1b9a")),
        ]

        for name, desc, color in games:
            banner = GameBannerWidget(name, desc, color)
            banner.play_clicked.connect(self.game_selected)
            banners_row.addWidget(banner)

        layout.addLayout(banners_row)

    # Paint event

    def paintEvent(self, event) -> None:
        """Light off-white background for the lobby screen."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f0f0eb"))
