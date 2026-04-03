from model.card import Card
from model.hand import Hand


class Player:
    """Represents a human or AI participant in the Deck Casino game.

    Tracks the player's dealt hand, collected cards, sweep count, and
    cumulative score across rounds.
    """

    DEFAULT_BANKROLL = 1000

    def __init__(self, name: str, is_ai: bool = False, difficulty: str = "hard",
                 bankroll: int = DEFAULT_BANKROLL) -> None:
        self._name = name
        self._is_ai = is_ai
        self._difficulty = difficulty  # "easy" | "medium" | "hard" (AI only)
        self._total_score = 0
        self._sweeps = 0
        self._bankroll = bankroll
        self.hand: Hand = Hand(owner=name)
        self._collection: list[Card] = []

    # Properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_ai(self) -> bool:
        return self._is_ai

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @property
    def total_score(self) -> int:
        return self._total_score

    @property
    def sweeps(self) -> int:
        return self._sweeps

    @property
    def collection(self) -> list[Card]:
        return list(self._collection)

    @property
    def bankroll(self) -> int:
        return self._bankroll

    # Bankroll management (Blackjack / Baccarat)

    def place_bet(self, amount: int) -> None:
        """Deduct a bet from the bankroll.

        Raises:
            ValueError: if amount <= 0 or exceeds the current bankroll.
        """
        if amount <= 0:
            raise ValueError("Bet must be greater than 0.")
        if amount > self._bankroll:
            raise ValueError(f"Bet {amount} exceeds bankroll {self._bankroll}.")
        self._bankroll -= amount

    def win(self, payout: int) -> None:
        """Add a payout to the bankroll (includes returned bet + winnings)."""
        self._bankroll += payout

    def lose(self) -> None:
        """No-op — bankroll was already reduced by place_bet()."""

    # Deck Casino scoring

    def add_to_collection(self, cards: list[Card] | Card) -> None:
        """Add one card or a list of cards to this player's collected pile."""
        if isinstance(cards, list):
            self._collection.extend(cards)
        else:
            self._collection.append(cards)

    def add_score(self, points: int) -> None:
        """Add points to the cumulative total score."""
        self._total_score += points

    def add_sweep(self) -> None:
        """Increment the sweep counter for this round."""
        self._sweeps += 1

    # Round management

    def reset_for_round(self) -> None:
        """Clear per-round state: hand, collection, and sweeps.

        total_score persists across rounds.
        """
        self.hand = Hand(owner=self._name)
        self._collection = []
        self._sweeps = 0

    # Dunder helpers

    def __str__(self) -> str:
        return f"{self._name} | Score: {self._total_score}"

    def __repr__(self) -> str:
        return f"Player(name='{self._name}', is_ai={self._is_ai}, difficulty='{self._difficulty}')"
