import json
import os

from model.card import Card
from model.deck import Deck
from model.hand import Hand
from model.player import Player

SAVE_FILE = "save_data.json"


class FileManager:
    """Serializes and restores full DeckCasinoGame state to/from JSON.

    Save format (save_data.json):
    {
      "turn_index": int,
      "table_cards":  [ {"suit": ..., "rank": ...}, ... ],
      "stock":        [ {"suit": ..., "rank": ...}, ... ],
      "players": [
        {
          "name": str,
          "is_ai": bool,
          "total_score": int,
          "sweeps": int,
          "hand":       [ {"suit": ..., "rank": ...}, ... ],
          "collection": [ {"suit": ..., "rank": ...}, ... ]
        },
        ...
      ],
      "move_history": [
        {
          "player":  str,
          "played":  str,        # e.g. "7 of Hearts"
          "action":  "take" | "place",
          "took":    [str, ...],  # card strings, empty for place
          "advice":  str          # improvement tip
        },
        ...
      ]
    }
    """

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @staticmethod
    def save(game, move_history: list[dict] | None = None) -> None:
        """Serialize full game state to SAVE_FILE.

        Args:
            game: A running DeckCasinoGame instance.
            move_history: Optional list of move records (see record_move()).
        """
        data = {
            "turn_index": game._turn_index,
            "table_cards": [FileManager._card_to_dict(c) for c in game._table_cards],
            "stock": [FileManager._card_to_dict(c) for c in game._deck._cards],
            "players": [
                {
                    "name": p.name,
                    "is_ai": p.is_ai,
                    "total_score": p.total_score,
                    "sweeps": p.sweeps,
                    "hand": [FileManager._card_to_dict(c) for c in p.hand.cards],
                    "collection": [FileManager._card_to_dict(c) for c in p.collection],
                }
                for p in game.players
            ],
            "move_history": move_history or [],
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    # ------------------------------------------------------------------
    # Load / restore
    # ------------------------------------------------------------------

    @staticmethod
    def load() -> "tuple | None":
        """Load and restore game state from SAVE_FILE.

        Returns:
            (DeckCasinoGame, move_history) tuple, or None if no save exists.
        """
        if not os.path.exists(SAVE_FILE):
            return None
        with open(SAVE_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        return FileManager.restore(data)

    @staticmethod
    def restore(data: dict) -> tuple:
        """Reconstruct a DeckCasinoGame from a saved state dict.

        Args:
            data: Parsed JSON dict produced by save().

        Returns:
            (DeckCasinoGame, move_history) tuple.
        """
        from model.deck_casino_game import DeckCasinoGame

        # Rebuild players with full state
        players: list[Player] = []
        for pd in data["players"]:
            p = Player(pd["name"], is_ai=pd["is_ai"])
            p._total_score = pd["total_score"]
            p._sweeps = pd["sweeps"]
            for cd in pd["hand"]:
                p.hand.add_card(FileManager._dict_to_card(cd))
            p._collection = [FileManager._dict_to_card(cd) for cd in pd["collection"]]
            players.append(p)

        # Bypass DeckCasinoGame.__init__ to avoid starting a fresh game
        game = object.__new__(DeckCasinoGame)
        game._players = players
        game._table_cards = [FileManager._dict_to_card(cd) for cd in data["table_cards"]]
        game._turn_index = data["turn_index"]
        game._last_taker = None  # not persisted; safe default

        # Restore stock pile preserving card order
        deck = object.__new__(Deck)
        deck._cards = [FileManager._dict_to_card(cd) for cd in data["stock"]]
        game._deck = deck

        return game, data.get("move_history", [])

    # ------------------------------------------------------------------
    # Move history helper
    # ------------------------------------------------------------------

    @staticmethod
    def record_move(
        player_name: str,
        played_card: Card,
        take: frozenset | None,
        table_before: list[Card],
    ) -> dict:
        """Build a move record with an improvement tip.

        Args:
            player_name: Name of the player who moved.
            played_card: Card played from hand.
            take: Cards taken from table, or None if placing.
            table_before: Table state before the move (used to generate advice).

        Returns:
            A dict suitable for appending to move_history.
        """
        action = "take" if take is not None else "place"
        took_strs = [str(c) for c in (take or [])]
        advice = FileManager._generate_advice(played_card, take, table_before)
        return {
            "player": player_name,
            "played": str(played_card),
            "action": action,
            "took": took_strs,
            "advice": advice,
        }

    @staticmethod
    def _generate_advice(
        played_card: Card, take: frozenset | None, table: list[Card]
    ) -> str:
        """Generate a simple improvement tip for the move made."""
        from model.casino_take_algorithm import CasinoTakeAlgorithm

        if take is None:
            # Placing — check if a take was actually available
            valid_takes = CasinoTakeAlgorithm.get_valid_takes(played_card, table)
            if valid_takes:
                return (
                    f"You placed {played_card}, but a take was available. "
                    "Consider taking cards to build your collection."
                )
            return f"No valid take with {played_card}; placing was the only option."

        # Taking — check for missed sweep
        if table and frozenset(table) != take:
            if CasinoTakeAlgorithm.is_valid_take(played_card, frozenset(table), table):
                return (
                    f"You could have swept the table with {played_card} "
                    "for a bonus sweep point!"
                )

        # Check if special cards were captured
        special_taken = [c for c in take if c.is_special()]
        if special_taken:
            names = ", ".join(str(c) for c in special_taken)
            return f"Good move — you captured high-value card(s): {names}."

        return "Solid take."

    # ------------------------------------------------------------------
    # Card serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _card_to_dict(card: Card) -> dict:
        return {"suit": card.suit, "rank": card.rank}

    @staticmethod
    def _dict_to_card(d: dict) -> Card:
        return Card(d["suit"], d["rank"])
