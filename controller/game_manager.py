from model.player import Player


class GameManager:
    """Central controller for the casino suite.

    Holds a registry of available Game instances, tracks the active game,
    and manages the player roster. Save/load and full game wiring are
    implemented in later weeks.
    """

    def __init__(self) -> None:
        self._games: dict = {}
        self._active_game = None
        self._players: list[Player] = []

    # Properties

    @property
    def active_game(self):
        return self._active_game

    @property
    def players(self) -> list[Player]:
        return list(self._players)

    # Player management

    def set_players(self, players: list[Player]) -> None:
        """Register the player roster for the next game."""
        self._players = players

    # Dunder helpers

    def __repr__(self) -> str:
        active = self._active_game.__class__.__name__ if self._active_game else "None"
        return f"GameManager(active_game={active}, players={len(self._players)})"
