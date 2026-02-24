import random

from model.card import Card, SUITS, RANKS


class Deck:
    """An ordered collection of 52 unique Card objects.

    cards / stock — the active draw pile; dealing pops from the end (top).

    Raises ValueError when deal() is called on an empty or too-small deck.
    """

    def __init__(self) -> None:
        self._cards: list[Card] = [
            Card(suit, rank) for suit in SUITS for rank in RANKS
        ]

    # Properties

    @property
    def cards(self) -> list[Card]:
        return self._cards

    @property
    def stock(self) -> list[Card]:
        """Alias used when referring to the stock pile in game logic."""
        return self._cards

    # Operations

    def shuffle(self) -> None:
        """Shuffle the draw pile in-place."""
        random.shuffle(self._cards)

    def deal(self, n: int = 1) -> list[Card]:
        """Remove and return n cards from the top of the deck.

        Raises:
            ValueError: if fewer than n cards remain.
        """
        if n < 1:
            raise ValueError(f"n must be at least 1, got {n}")
        if len(self._cards) < n:
            raise ValueError(
                f"Cannot deal {n} card(s): only {len(self._cards)} remaining"
            )
        dealt: list[Card] = []
        for _ in range(n):
            dealt.append(self._cards.pop())
        return dealt

    def is_empty(self) -> bool:
        """Return True when no cards remain."""
        return len(self._cards) == 0

    # Dunder helpers

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self) -> str:
        return f"Deck({len(self._cards)} cards remaining)"
